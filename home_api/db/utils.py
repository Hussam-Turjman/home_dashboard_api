import datetime
import secrets
import string

month_2_id = {'Jan': 1, 'Feb': 2,
              'Mar': 3, 'Apr': 4,
              'May': 5, 'Jun': 6,
              'Jul': 7, 'Aug': 8,
              'Sep': 9, 'Oct': 10,
              'Nov': 11, 'Dec': 12}
id_2_month = {v: k for k, v in month_2_id.items()}


def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month


def create_dates_labels(min_start_year, min_start_month, month_diff, end_month, end_year,
                        include_last_month, to_dates):
    x_labels = []
    year = min_start_year
    for month in range(min_start_month, min_start_month + month_diff):
        month = month % 12

        if month == 0:
            month = 12

        x_labels.append(f"{id_2_month[month]} {year}")
        if month == 12:
            year += 1
    if include_last_month:
        x_labels.append(f"{id_2_month[end_month]} {end_year}")
    if to_dates:
        x_labels = [datetime.datetime.strptime(
            label, "%b %Y").date() for label in x_labels]
    return x_labels


def find_invoice_by_counter_id(invoices, counter_id_in):
    for idx, invoice in enumerate(invoices):
        label = invoice["label"]
        label = label.split("-")
        counter_id = label[1]
        if counter_id == counter_id_in:
            return idx
    return None


def generate_password(length: int = 20, fixed=False):
    if fixed:
        return "sf923_rFfs;@e3f"
    # Define the alphabet to contain all printable characters except whitespaces
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password


def create_username(first_name: str, last_name: str, last_id: int):
    username = f"{first_name.lower()[:2]}{last_name.lower()[:2]}{last_id + 1}"
    return username


__all__ = ["generate_password",
           "create_username",
           "diff_month",
           "month_2_id",
           "id_2_month",
           "find_invoice_by_counter_id",
           "create_dates_labels"]
