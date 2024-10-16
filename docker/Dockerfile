FROM postgres:latest

LABEL Author="Hussam Turjman" \
      Description="This is a custom PostgreSQL image with the home dashboard dependencies installed" \
      Version="0.0" \
      Email="hussam.turjman@gmail.com"

ARG DB_USER=hussam
ARG DB_USER_ID=1000
ARG DB_USER_GID=1000
ARG DB_PASS=verystrongpassword
ARG DB_NAME=home_dashboard

# Create a new user and group
RUN groupadd -g $DB_USER_GID $DB_USER && \
    useradd -m -u $DB_USER_ID -g $DB_USER_GID $DB_USER

# Add user to postgres group
RUN usermod -aG postgres $DB_USER

# Start the postgres server
RUN apt-get update && apt-get install -y  systemctl sudo
# Install vim
RUN apt-get install -y vim
RUN apt-get install -y git build-essential
RUN apt-get install -y wget htop sqlite3


RUN usermod -aG sudo $DB_USER && \
    echo "$DB_USER ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers


# RUN pg_isready
# change to the new user
USER $DB_USER
ENV HOME_DIR=/home/$DB_USER

WORKDIR $HOME_DIR



# Copy init_db_server.sh to the container
COPY ./init_db_server.sh $HOME_DIR/init_db_server.sh

# Export DB_USER and DB_PASS and DB_NAME
ENV DB_USER=$DB_USER
ENV DB_PASS=$DB_PASS
ENV DB_NAME=$DB_NAME

# Put ./init_db_server.sh .bashrc
RUN echo "source $HOME_DIR/init_db_server.sh" >> $HOME_DIR/.bashrc


# Download and install miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
RUN bash miniconda.sh -b -p $HOME_DIR/miniconda
RUN rm miniconda.sh
ENV PATH=$HOME_DIR/miniconda/bin:$PATH
RUN conda --version
ENV CONDA_PATH=$HOME_DIR/miniconda

# Add conda initialization to .bashrc
RUN echo "# >>> conda initialize >>>" >> $HOME_DIR/.bashrc && \
    echo "# !! Contents within this block are managed by 'conda init' !!" >> $HOME_DIR/.bashrc && \
    echo "__conda_setup=\"\$('$CONDA_PATH/bin/conda' 'shell.bash' 'hook' 2> /dev/null)\"" >> $HOME_DIR/.bashrc && \
    echo "if [ \$? -eq 0 ]; then" >> $HOME_DIR/.bashrc && \
    echo "    eval \"\$__conda_setup\"" >> $HOME_DIR/.bashrc && \
    echo "else" >> $HOME_DIR/.bashrc && \
    echo "    if [ -f \"$CONDA_PATH/etc/profile.d/conda.sh\" ]; then" >> $HOME_DIR/.bashrc && \
    echo "        . \"$CONDA_PATH/etc/profile.d/conda.sh\"" >> $HOME_DIR/.bashrc && \
    echo "    else" >> $HOME_DIR/.bashrc && \
    echo "        export PATH=\"$CONDA_PATH/bin:\$PATH\"" >> $HOME_DIR/.bashrc && \
    echo "    fi" >> $HOME_DIR/.bashrc && \
    echo "fi" >> $HOME_DIR/.bashrc && \
    echo "unset __conda_setup" >> $HOME_DIR/.bashrc && \
    echo "# <<< conda initialize <<<" >> $HOME_DIR/.bashrc

# Upgrade pip
RUN pip install --upgrade pip

COPY ./requirements.txt $HOME_DIR/requirements.txt
RUN pip install -r ./requirements.txt
