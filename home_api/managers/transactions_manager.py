import calendar
import datetime
import json
import os
import re
import uuid
from typing import List, Dict

import numpy as np
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm.session import Session as SQLSession

from .errors import ManagerErrors
from .return_wrapper import return_wrapper
from ..db.tables import BankTransaction
from ..db.utils import dates_to_labels
from ..logger import logger
from ..pydantic_models.account import MonthExpensesTagModel

categories = {
    "Shopping": {
        "Supermarket": ["rewe", "edeka", "aldi", "lidl", "penny", "kaufland"],
        "Drugstore": ["dm", "rossmann", "müller drogerie"],
        "Online Retail": ["amazon", "ebay", "zalando", "otto", "shein", "apple services"],
        "Retail": ["woolworth"],
        "Luggage & Bags": ["koffer", "trolley", "handtasche", "bags"],
        "Clothing": ["h&m", "c&a", "C+A", "h+m", "peek & cloppenburg", "about you"],
        "Electronics": ["mediamarkt", "saturn", "cyberport", "notebooksbilliger"],
        "Furniture & Living": ["ikea", "roller", "mömax", "porta"],
        "Printing Service": ["bomhoff GmbH"],
    },
    "Living Expenses": {
        "Rent": ["miete", "wohnungs", "vermieter"],
        "Deposit": ["kaution", "mietkaution"],
        "Utilities": ["nebenkosten", "heizkosten"],
        "Electricity & Gas": ["strom", "gas", "energie", "eprimo", "vattenfall", "e.on", "swb"],
        "Water": ["wasserwerke", "wasser", "swb"],
        "Broadcast Fee": ["rundfunk", "beitragsservice", "ard zdf"],
        "Telecom": ["telekom", "vodafone", "o2", "telefon", "internet"],
    },
    "Transport": {
        "Public Transport": ["bahn", "db", "mvv", "vbn", "vgn", "rnv"],
        "Gas Station": ["tankstelle", "esso", "aral", "shell", "jet", "station"],
        "Parking": ["parken", "parkgebühr"],
        "Car (Maintenance/Insurance)": ["versicherung", "kfz", "autowerkstatt", "dekra", "tüv"]
    },
    "Leisure & Entertainment": {
        "Streaming": ["netflix", "spotify", "disney", "wow", "youtube"],
        "Gaming": ["steam", "epic games", "playstation", "xbox", "nintendo"],
        "Cinema & Events": ["kino", "eventim", "ticketmaster"],
        "Books & Media": ["thalia", "hugendubel", "bücher"]
    },
    "Travel": {
        "Flight": ["lufthansa", "ryanair", "eurowings", "flug"],
        "Hotel": ["hotel", "booking.com", "airbnb"],
        "Train": ["bahn", "db"],
        "Public Transport Abroad": ["metro", "underground", "bus", "transport"]
    },
    "Health": {
        "Pharmacy": ["apotheke"],
        "Doctor": ["arzt", "zahnarzt", "praxis", "labor"],
        "Health Insurance": ["krankenkasse", "aok", "barmer", "dakn", "versicherung"],
        "Gym": ["fitx", "mcfit", "fitness"]
    },
    "Finance": {
        "Bank Fees": ["kontoführungsgebühr", "gebühr", "bank"],
        "Interest": ["zins", "zinsen"],
        "Loan Repayment": ["kredit", "ratenzahlung"],
        "Saving & Investing": ["etf", "aktie", "trade", "depot", "zins"]
    },
    "Food & Drinks": {
        "Restaurant": ["restaurant", "essen", "gastronomie"],
        "Café": ["café", "kaffee"],
        "Delivery Service": ["lieferando", "wolt", "ubereats"],
        "Bakery": ["behrens-meyer", "baker", "bäckerei", "brot", "brötchen", "baecker", "backwerk", "haferkamp",
                   "von allwoerden"],
    },
    "Household & DIY": {
        "Hardware Store": ["hornbach", "obi", "toom", "bauhaus"],
        "Garden Supplies": ["garten", "pflanzen"],
        "Cleaning Supplies": ["putzmittel", "reinigungsmittel", "reiniger"]
    },
    "Education": {
        "Courses & Further Education": ["kurs", "schule", "weiterbildung", "udemy", "masterclass"],
        "Books & Materials": ["lehrbuch", "skript", "studienmaterial"]
    },
    "Donations & Gifts": {
        "Donation": ["spende", "donation", "ngo", "verein"],
        "Gift": ["geschenk", "present", "gutschein"]
    },
    "Income": {
        "Salary": ["gehalt", "lohn", "lohn/gehalt"],
        "Money Transfer": ["überweisung", "zahlungseingang", "eingang"],
        "Refund": ["rückzahlung", "erstattung", "gutschrift"],
        "Cash Deposit": ["bargeldeinzahlung"],
    },
    "Other": {
        "Uncategorized": [],
        "Cash Withdrawal": ["geldautomat", "atm", "barabhebung", "bargeldauszahlung"],
        "Card Charge": ["ladung mensacard", "mensacard", "mensacard aufladung"],
    }
}

umlaut_map = {
    'ä': 'ae',
    'ö': 'oe',
    'ü': 'ue',
    'ß': 'ss'
}


def create_summary(df_in):
    summary_out = df_in.groupby(['Category', 'Subcategory']).agg(
        Total_Amount=('Amount', 'sum'),
        Transaction_Count=('Amount', 'count'),
        Min_Booking_Date=('Booking Date', 'min'),
        Max_Booking_Date=('Booking Date', 'max'),
        Min_Amount=('Amount', 'min'),
        Max_Amount=('Amount', 'max'),
        Avg_Amount=('Amount', 'mean'),
        Median_Amount=('Amount', 'median'),
        Unique_Keywords=('Keyword', lambda x: ", ".join(
            x.unique()) if x.notnull().any() else None),
    ).reset_index()
    # convert the Booking Date to datetime
    summary_out['Min_Booking_Date'] = pd.to_datetime(
        summary_out['Min_Booking_Date'])
    summary_out['Max_Booking_Date'] = pd.to_datetime(
        summary_out['Max_Booking_Date'])
    # calculate total number of days between min and max booking date
    # summary_out['Days'] = (summary_out['Max_Booking_Date'] - summary_out['Min_Booking_Date']).dt.days
    # round all float values to 2 decimal places
    summary_out = summary_out.round({
        'Total_Amount': 2,
        'Avg_Amount': 2,
        'Median_Amount': 2,
        'Min_Amount': 2,
        'Max_Amount': 2,
    })
    return summary_out


def categorize(description, amount):
    desc = description.lower()
    for category, subcats in categories.items():
        for subcat, keywords in subcats.items():
            # if any(keyword in desc for keyword in keywords):
            for keyword in keywords:
                # Replace umlauts with their replacements
                for umlaut, replacement in umlaut_map.items():
                    keyword = keyword.replace(umlaut, replacement)
                keyword = keyword.lower()
                if keyword in desc:
                    if category == "Income" and amount < 0:
                        continue
                    if category != "Income" and amount > 0:
                        continue
                    if subcat == "Deposit" and amount > 0:
                        continue

                    return pd.Series([category, subcat, keyword])
    return pd.Series(["Other", "Uncategorized", None])


def convert_to_utf8(filepath: str, output_filepath: str) -> pd.DataFrame:
    with open(filepath, "r", encoding="latin1") as f:
        content = f.read()
        # Replace umlauts with their replacements
        for umlaut, replacement in umlaut_map.items():
            content = content.replace(umlaut, replacement)

    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(content)
    df = pd.read_csv(output_filepath, sep=";", encoding="utf-8")
    # remove Auftragskonto
    df = df.drop(columns=["Auftragskonto"])
    df["Buchungstag"] = pd.to_datetime(df["Buchungstag"], format="%d.%m.%y")
    df["Valutadatum"] = pd.to_datetime(df["Valutadatum"], format="%d.%m.%y")

    # Fill empty Valutadatum with Buchungstag
    df["Valutadatum"] = df["Valutadatum"].fillna(df["Buchungstag"])
    df['Betrag'] = df['Betrag'].str.replace(',', '.').astype(float)
    # strip whitespace and newline characters from all string columns
    string_columns = df.select_dtypes(include=['object']).columns
    for col in string_columns:
        df[col] = df[col].str.strip()

    # replace nan with empty string in all string columns
    df[string_columns] = df[string_columns].fillna('')
    # for all string columns split and join with space
    for col in string_columns:
        df[col] = df[col].str.split().str.join(' ')

    combined_columns = ['Buchungstext', 'Verwendungszweck', 'Glaeubiger ID', 'Mandatsreferenz',
                        'Kundenreferenz (End-to-End)', 'Sammlerreferenz', 'Lastschrift Ursprungsbetrag',
                        'Auslagenersatz Ruecklastschrift', 'Beguenstigter/Zahlungspflichtiger', 'Kontonummer/IBAN',
                        'BIC (SWIFT-Code)', 'Info']
    # combine all columns in combined_columns
    new_column_name = "Description"
    df[new_column_name] = df[combined_columns].astype(
        str).agg(' '.join, axis=1)
    # remove the combined columns
    df = df.drop(columns=combined_columns)
    new_column_names = {
        "Buchungstag": "Booking Date",
        "Valutadatum": "Value Date",
        "Betrag": "Amount",
        "Waehrung": "Currency",
        "Description": "Description",
    }
    df = df.rename(columns=new_column_names)
    # remove nan keyword from Description
    df["Description"] = df["Description"].str.replace("nan", "")

    # Remove all IBAN and similar patterns from Description
    patterns = [
        r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}\b',  # IBAN
        r'\b\d{26}\b',  # Numeric IBAN
        r'\bELV\d{8}\b',  # ELV pattern
        r'\b[A-Z]\d{21}\b',  # Pattern with one letter followed by 21 digits
        r'\b\d{27}\b',  # 27-digit pattern
        r'\b\d{35}\b',  # 35-digit pattern
        # Pattern with two letters followed by 32 digits
        r'\b[A-Z]{2}\d{32}\b',
        r'\b[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?\b',  # SWIFT/BIC code
        r'\b[A-Z]{2}\d{8}\b',  # Pattern with two letters followed by 8 digits
        r'\bBLZ\d{8}\b',  # BLZ pattern
        r'\b\d+\b',  # Any standalone number,
        # Pattern with 33 digits followed by two letters
        r'\b\d{33}[A-Z]{2}\b',
        # Pattern with two letters followed by 34 digits
        r'\b[A-Z]{2}\d{33}\b',
        r'^\d[A-Z0-9]{6}\d{19}[A-Z]{6}\d{3}$',
        # Pattern with 6 digits followed by 19 alphanumeric characters, 6 letters, and 3 digits
    ]

    for pattern in patterns:
        df["Description"] = df["Description"].apply(
            lambda x: re.sub(pattern, '', x))
    # remove Umsatz gebucht
    df["Description"] = df["Description"].str.replace("Umsatz gebucht", "")

    df["Description"] = df["Description"].str.split().str.join(' ')

    df.to_csv(output_filepath, encoding="utf-8", index=False, sep=";")
    return df


class TransactionsManager(object):
    db_session: SQLSession

    def __init__(self, db_session: SQLSession):
        self.db_session = db_session
        self.uploaded_files_dir = os.path.join(
            f"tmp", "home_dashboard_api", "uploaded_files")
        self.create_uploaded_files_dir()

    def create_uploaded_files_dir(self):
        """
        Create the uploaded files directory if it doesn't exist.
        """
        if not os.path.exists(self.uploaded_files_dir):
            os.makedirs(self.uploaded_files_dir)

    def parse_file(self, filename: str, filetype: str, filesize: int, content: bytes, user_id: int) -> dict:
        """
        Parse a file and return the contents.
        """
        self.create_uploaded_files_dir()
        base_dir = os.path.join(self.uploaded_files_dir, filename)

        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        filepath = os.path.join(base_dir, filename)
        output_filepath_utf8 = os.path.join(base_dir, f"{filename}.utf8.csv")
        output_filepath_categorized = os.path.join(
            base_dir, f"{filename}.categorized.csv")
        output_filepath_summary = os.path.join(
            base_dir, f"{filename}.summary.csv")
        metadata_filepath = os.path.join(base_dir, f"{filename}.metadata.json")

        if os.path.exists(filepath):
            os.remove(filepath)
        if os.path.exists(output_filepath_utf8):
            os.remove(output_filepath_utf8)
        if os.path.exists(output_filepath_categorized):
            os.remove(output_filepath_categorized)
        if os.path.exists(output_filepath_summary):
            os.remove(output_filepath_summary)
        if os.path.exists(metadata_filepath):
            os.remove(metadata_filepath)

        with open(filepath, "wb") as f:
            f.write(content)

        # create utf8 file
        df = convert_to_utf8(filepath, output_filepath_utf8)

        # Apply categorization
        df[['Category', 'Subcategory', "Keyword"]] = df.apply(
            lambda x: categorize(x['Description'], x['Amount']), axis=1)

        df.to_csv(output_filepath_categorized, sep=";", index=False)

        summary = create_summary(df)
        summary.to_csv(output_filepath_summary, sep=";", index=False)

        metadata = {
            "filename": filename,
            "filetype": filetype,
            "filesize": filesize,
            "filepath": filepath,
            "output_filepath_utf8": output_filepath_utf8,
            "output_filepath_categorized": output_filepath_categorized,
            "output_filepath_summary": output_filepath_summary,
            "created_at": datetime.datetime.now().isoformat(),
        }
        # save metadata to file
        with open(metadata_filepath, "w") as f:
            json.dump(metadata, f, indent=4)

        logger.info(
            f"Creating bank transactions for user {user_id} from file {filename}")
        # save to db. Only entries which don't exist in the db
        # get all entries in the db
        for index, row in df.iterrows():
            booking_date = row["Booking Date"].date()
            value_date = row["Value Date"].date()
            amount = row["Amount"]
            currency = row["Currency"]
            description = row["Description"]
            category = row["Category"]
            subcategory = row["Subcategory"]
            keyword = "" if row["Keyword"] is None else row["Keyword"]

            # check if entry exists in the db
            transaction = self.db_session.query(BankTransaction).filter(

                BankTransaction.booking_date == booking_date,
                BankTransaction.value_date == value_date,
                BankTransaction.amount == amount,
                BankTransaction.currency == currency,
                BankTransaction.description == description,
                BankTransaction.category == category,
                BankTransaction.subcategory == subcategory,
                BankTransaction.keyword == keyword,
                BankTransaction.user_id == user_id
            ).first()
            if transaction is None:
                transaction = BankTransaction(
                    id=str(uuid.uuid4()),
                    booking_date=booking_date,
                    value_date=value_date,
                    amount=amount,
                    currency=currency,
                    description=description,
                    category=category,
                    subcategory=subcategory,
                    keyword=keyword,
                    user_id=user_id,

                )
                self.db_session.add(transaction)

        self.db_session.commit()

    def get_bank_transactions(self, user_id: int):
        """
        Get all bank transactions for a user
        Parameters
        ----------
        user_id

        Returns
        -------

        """
        transactions = self.db_session.query(BankTransaction).filter(
            BankTransaction.user_id == user_id
        ).all()
        return transactions

    def get_month_expenses(self, user_id, month, year):
        results = []
        date = datetime.date(year, month, 1)

        # Group by tag and sum amount
        query = (self.db_session.query(BankTransaction.category.label("label"),
                                       func.sum(BankTransaction.amount).label("value")).
                 filter(BankTransaction.user_id == user_id).
                 # Date between start and end
                 filter(BankTransaction.booking_date <= date).
                 # filter(BankTransaction.end_date >= date).
                 group_by(BankTransaction.category).
                 all())
        idx = 0
        for tag, value in query:
            if value >= 0:
                continue
            results.append(MonthExpensesTagModel(
                id=idx, value=abs(value), label=tag))
            idx += 1
        return results

    def get_month_expenses_and_savings(self, user_id, month, year,
                                       ignore_invalid_income=True,
                                       allow_all_zeros=True) -> List[
            MonthExpensesTagModel]:
        expenses = self.get_month_expenses(user_id, month, year)
        total_expenses = sum([expense.value for expense in expenses])
        date = datetime.date(year, month, 1)
        results = []
        # Get income
        income = (self.db_session.query(func.sum(BankTransaction.amount).label("income")).
                  filter(BankTransaction.user_id == user_id).
                  filter(BankTransaction.booking_date <= date).
                  # filter(BankTransaction.end_date >= date).
                  filter(BankTransaction.amount > 0).
                  first())
        if income and income[0] is not None:
            total_income = income[0]
            # max(total_income - total_expenses, 0)
            savings = total_income - total_expenses
            results.append(MonthExpensesTagModel(
                id=0, value=savings, label="Savings"))
            results.append(MonthExpensesTagModel(
                id=1, value=total_expenses, label="Expenses"))
            results.append(MonthExpensesTagModel(
                id=2, value=total_income, label="Income"))
        elif ignore_invalid_income:
            results.append(MonthExpensesTagModel(
                id=0, value=-total_expenses, label="Savings"))
            results.append(MonthExpensesTagModel(
                id=1, value=total_expenses, label="Expenses"))
            results.append(MonthExpensesTagModel(
                id=2, value=0, label="Income"))
        if not allow_all_zeros:
            results = [result for result in results if result.value != 0]
        return results

    def _get_overview_chart(self, user_id,
                            start_month=None,
                            start_year=None,
                            end_month=None,
                            end_year=None,
                            include_last_month=False,
                            apply_cumulative_on_expenses=True,
                            apply_cumulative_on_income=True,
                            apply_cumulative_on_savings=True):

        amount_booking_date_entries = self.db_session.query(
            BankTransaction.booking_date,
            BankTransaction.amount,
            BankTransaction.subcategory
        ).filter(
            BankTransaction.user_id == user_id,
        ).all()
        if len(amount_booking_date_entries) == 0:
            current_date = datetime.date.today()
            return {
                "x_labels": [],
                "cumulative_savings": [],
                "cumulative_expenses": [],
                "cumulative_income": [],
                "start_month": current_date.month,
                "start_year": current_date.year,
                "end_month": current_date.month,
                "end_year": current_date.year
            }
        # convert to pandas dataframe
        df = pd.DataFrame(amount_booking_date_entries, columns=[
                          "Booking Date", "Amount", "Subcategory"])
        df["Booking Date"] = pd.to_datetime(df["Booking Date"])

        start_date = df["Booking Date"].min().replace(day=1)
        end_date = df["Booking Date"].max()
        # set end_date day to last day of month
        last_day = calendar.monthrange(end_date.year, end_date.month)[1]
        end_date = end_date.replace(day=last_day)

        dates = pd.date_range(start_date, end_date, freq='1ME')

        date_ranges = pd.DataFrame({
            "Start_Date": dates[:-1],
            "End_Date": dates[1:]
        })
        date_ranges["Start_Date"] = pd.to_datetime(date_ranges["Start_Date"])
        date_ranges["End_Date"] = pd.to_datetime(date_ranges["End_Date"])
        results = date_ranges.apply(
            lambda row: pd.Series({
                "Income": df[(df["Booking Date"] >= row["Start_Date"]) & (df["Booking Date"] <= row["End_Date"]) & (
                    df["Amount"] > 0)  # & (df["Subcategory"] == "Salary")
                ]["Amount"].sum(),
                "Expenses": df[(df["Booking Date"] >= row["Start_Date"]) & (df["Booking Date"] <= row["End_Date"]) & (
                    df["Amount"] < 0)]["Amount"].sum()
            }),
            axis=1
        )
        results["Savings"] = results["Income"] + results["Expenses"]
        # make expenses positive
        results["Expenses"] = results["Expenses"].abs()
        summary = []
        for idx, row in date_ranges.iterrows():
            # logger.info(
            #    f"From {row['Start_Date'].date()} to {row['End_Date'].date()}: Income: {results.loc[idx, 'Income']:.2f} EUR, Expenses: {results.loc[idx, 'Expenses']:.2f} EUR, Savings: {results.loc[idx, 'Savings']:.2f} EUR")
            summary.append({
                "Start_Date": row["Start_Date"].date(),
                "End_Date": row["End_Date"].date(),
                "Income": results.loc[idx, 'Income'],
                "Expenses": results.loc[idx, 'Expenses'],
                "Savings": results.loc[idx, 'Savings']
            })
        summary = pd.DataFrame(summary)
        # remove all data which dates are not in the range

        cumulative_savings = summary["Savings"].tolist()
        cumulative_expenses = summary["Expenses"].tolist()
        cumulative_income = summary["Income"].tolist()

        if apply_cumulative_on_savings:
            cumulative_savings = np.cumsum(cumulative_savings).tolist()
        if apply_cumulative_on_expenses:
            cumulative_expenses = np.cumsum(cumulative_expenses).tolist()
        if apply_cumulative_on_income:
            cumulative_income = np.cumsum(cumulative_income).tolist()
        start_month = start_date.month
        start_year = start_date.year
        end_month = end_date.month
        end_year = end_date.year
        summary["Savings"] = cumulative_savings
        summary["Expenses"] = cumulative_expenses
        summary["Income"] = cumulative_income
        summary = summary[(summary["Start_Date"] >= start_date.date()) & (
            summary["Start_Date"] <= end_date.date())]
        logger.info(f"\n{summary}")
        x_labels = dates_to_labels(summary["Start_Date"])
        cumulative_savings = summary["Savings"].tolist()
        cumulative_expenses = summary["Expenses"].tolist()
        cumulative_income = summary["Income"].tolist()
        return {
            "x_labels": x_labels,
            "cumulative_savings": cumulative_savings,
            "cumulative_expenses": cumulative_expenses,
            "cumulative_income": cumulative_income,
            "start_month": start_month,
            "start_year": start_year,
            "end_month": end_month,
            "end_year": end_year

        }

    @return_wrapper()
    def get_overview_chart(self, user_id,
                           start_month=None,
                           start_year=None,
                           end_month=None,
                           end_year=None,
                           include_last_month=False,
                           apply_cumulative_on_expenses=True,
                           apply_cumulative_on_income=True,
                           apply_cumulative_on_savings=True
                           ):
        res = self._get_overview_chart(user_id=user_id,
                                       start_month=start_month,
                                       start_year=start_year,
                                       end_month=end_month,
                                       end_year=end_year,
                                       include_last_month=include_last_month,
                                       apply_cumulative_on_expenses=apply_cumulative_on_expenses,
                                       apply_cumulative_on_income=apply_cumulative_on_income,
                                       apply_cumulative_on_savings=apply_cumulative_on_savings
                                       )
        logger.info(f"Transactions overview chart: {res}")
        return res

    def get_total_expenses_and_savings(self, user_id) -> List[
            MonthExpensesTagModel]:
        total_expenses = self.db_session.query(
            func.sum(BankTransaction.amount).label("total_expenses")) \
            .filter(BankTransaction.user_id == user_id,
                    BankTransaction.amount < 0).first()
        if total_expenses and total_expenses[0] is not None:
            total_expenses = total_expenses[0]
        else:
            total_expenses = 0
        total_income = self.db_session.query(
            func.sum(BankTransaction.amount).label("total_income")) \
            .filter(BankTransaction.user_id == user_id,
                    BankTransaction.amount > 0).first()
        if total_income and total_income[0] is not None:
            total_income = total_income[0]
        else:
            total_income = 0
        total_savings = total_income + total_expenses
        results = [
            MonthExpensesTagModel(
                id=0, value=total_savings, label="Savings"),
            MonthExpensesTagModel(
                id=1, value=abs(total_expenses), label="Expenses"),
            MonthExpensesTagModel(
                id=2, value=total_income, label="Income")
        ]

        return results

    def get_category_expenses_and_savings(self, user_id) -> List[
            MonthExpensesTagModel]:
        results = []
        # Get all categories
        all_categories = self.db_session.query(BankTransaction.category).filter(
            BankTransaction.user_id == user_id).distinct().all()
        all_categories = [category[0] for category in all_categories]
        # sum all amount for each category
        for idx, category in enumerate(all_categories):
            category_sum = self.db_session.query(
                func.sum(BankTransaction.amount).label("category_sum")) \
                .filter(BankTransaction.user_id == user_id,
                        BankTransaction.category == category).first()
            if category_sum and category_sum[0] is not None:
                category_sum = category_sum[0]
            else:
                category_sum = 0

            results.append(
                MonthExpensesTagModel(
                    id=idx, value=category_sum, label=str(category))
            )
        return results

    def get_subcategory_expenses_and_savings(self, user_id) -> List[Dict[str, List[MonthExpensesTagModel]]]:
        results = []
        # Get all categories
        all_categories = self.db_session.query(BankTransaction.category).filter(
            BankTransaction.user_id == user_id).distinct().all()
        all_categories = [category[0] for category in all_categories]
        # sum all amount for each subcategory
        for category in all_categories:
            subcategory_results = []
            all_subcategories = self.db_session.query(BankTransaction.subcategory).filter(
                BankTransaction.user_id == user_id,
                BankTransaction.category == category).distinct().all()
            all_subcategories = [subcategory[0]
                                 for subcategory in all_subcategories]
            for idx, subcategory in enumerate(all_subcategories):
                subcategory_sum = self.db_session.query(
                    func.sum(BankTransaction.amount).label("subcategory_sum")) \
                    .filter(BankTransaction.user_id == user_id,
                            BankTransaction.category == category,
                            BankTransaction.subcategory == subcategory).first()
                if subcategory_sum and subcategory_sum[0] is not None:
                    subcategory_sum = subcategory_sum[0]
                else:
                    subcategory_sum = 0
                subcategory_results.append(
                    MonthExpensesTagModel(
                        id=idx, value=subcategory_sum, label=str(subcategory))
                )
            results.append({
                "category": category,
                "subcategories": subcategory_results
            })
        return results


__all__ = ["TransactionsManager"]
