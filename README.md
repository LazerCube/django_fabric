# Django Fabric Automating frequent deployment task in Django with Fabric - WIP

A git repository to automate frquent deployment tasks in django using Fabric. This repository can be used to turn a clean install of a Debian-based Linux OS into a working web server  capable of serving a Django project with only minimal configuring and pre-setup.

## Getting Started

A `project_settings.json` and `database_settings.json` file are required and should be customized for each project. **git will ignore these files as they contain sensitve information about the server.**

### Prerequisites

What things you need to install use the software

-   Fabric (Client)
-   Openssh-server (Server)

#### Installing fabric

Fabric needs to be installed on the local machine. An easy way of installing Fabric is by using the default operating system package manager `aptitude`.

```
sudo aptitude install fabric

# Alternatively, you can also use *pip*:
# pip install fabric
```

#### Installing/Setup for SSH

Fabric allows for excellent integration with SSH that allows for streamlining tasks using simple python scripts. SSH is also a key part of any server configuration.

##### Creating new user

By default the fabric file will want sign in as a user called "django", but this could be replace with any username you like as lone as you remember to update the fab file to the same name.

```
sudo adduser django
```

The fabric file will need to be able to run with with administrative privilege in order to install successfully. To allow our new new user to do this we need to add it to the "sudo" group.

```
sudo gpasswd -a django sudo
```

##### Installing SSH

```
sudo apt-get update
sudo apt-get install openssh-server
```

Disable ufw to stop it creating items in iptables

```
sudo ufw disable
```

#####  Adding Public Key Authentication

To generate a new key pair, enter the following command at the terminal of your local machine (ie. your computer)

```
shh-keygen
```

Next copy the Public key on your local machine so we can add it to our server. ssh keys are normally generated to `~/.ssh/id_rsa.pub`. To print your public key in your local machine run.

```
cat ~/.ssh/id_rsa.pub
```

This will print your public SSH key, select and copy it to your clipboard. To enable the user of a SSH key to authenticate, you must add the public key to a special file in your user's home directory.

_On the Server_, enter.

```
su - django
```

Create a new directory called `.ssh` and restrict its permissions.

```
mkdir .ssh
chmod 700 .ssh
```

Now open a file in .ssh called authorized_keys with a text editor. We will use `nano` to edit the file.

```
nano .ssh/authorized_keys
```

Now insert your public key here and exit `nano`. In order to restrict permissions to authorized_keys we run.

```
chmod 600 .ssh/authorized_keys
```

You can now run `exit` to logout of your new user.


##### Configuring SSH

Begin by creating a backup of the default config, just in case. Next, open the configuration file with your favorite text editor (for this example we will use nano).

```
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config_backup
sudo nano /etc/ssh/sshd_config
```

Then, change default port number. This is a basic step that helps to keep your server as secure as possible.
```
#Before
Port 22

# After
Port 25000
```

Next, we need to disable root login, Modify this line to "no" or "without-password" like this to disable root login.

```
#Before
PermitRootLogin yes

#After
PermitRootLogin without-password
```

We can also disable password authentication and allow only SSH keys, giving your server some extra security. Set the following settings to the following values. If these settings are already in the file, set them to "no" rather than add new lines.

```
#Before
PasswordAuthentication yes

#After
PasswordAuthentication no
```

Reload SSH

```
service ssh restart
```

#### Mail service for Fail2ban

##### Hosts

Change your hosts in `/etc/hosts`

```
127.0.0.1 <localhost.localdomain> localhost <yourhostname>
```

##### Testing sendmail

```
echo "Subject: test" | sendmail -v me@my-domain.com
```

## Config Files

### project_settings.json

```
{
    "project_name": "",
    "git_repository": "",
    "stages": {
        "stable": {
            "name": "stable",
            "host": "",
            "user": "",
            "vcs_branch": "master",
            "venv_directory": "",
            "requirements_file": "",
            "code_src_directory": "",
            "restart_command": ""
        },
        "development": {
            "name": "stage",
            "host": "",
            "user": "",
            "vcs_branch": "",
            "venv_directory": "",
            "requirements_file": "",
            "code_src_directory": "",
            "restart_command": ""
        }
    },
    "local": {
        "code_src_directory": "",
        "venv_python_executable": ""
    },
    "configs": {
        "fail2ban": {
            "config_src": "django_fabric/config/jail.local",
            "config_directory": "/etc/fail2ban/"
        },
        "nginx": {
            "config_src": "django_fabric/config/nginx.conf",
            "config_directory": "/etc/nginx"
        },
        "gunicorn": {
            "config_src": "django_fabric/bin/gunicorn.service",
            "config_directory": "/etc/systemd/system"
        }
    }
}

```

We keep a settings module with versioned settings files for each stage.

```
{
    "project_name": ,
    "vcs_type": ,
    "git_repository": ,
}
```

**project name** - Name of the django project
**git_repository** - Address to the git repository

```
{
    "stable": {
        "name": "stable",
        "host": "",
        "user": "",
        "vcs_branch": "",
        "venv_directory": "",
        "requirements_file": "",
        "code_src_directory": "",
        "restart_command": ""
    }
}
```

**name** - Name of stage
**host** - Hostname or IP address of your server
**user** - User to run your tasks
**vcs_branch** - Branch to use for this installation; set according to your naming conventions, we stick to 'stable' and 'development'
**venv_directory** - Path to your virtualenv; needed to run tasks in installation context
**requirement_file** - Path to requirements file for this installation
**code_src_directory** - Path to directory containing source code, in particular your manage.py file
**restart_command** - We use supervisord for keeping track of processes; in this case the command could be 'supervisorctl restart project_name'

The last section is specifically for local environment to provide paths for running tests:

```
{
    "local": {
        "code_src_directory": "",
        "venv_python_executable": ""
    }
}
```

**code_src_directory** - Path to directory containing source code, in particular your manage.py file
**venv_python_executable** - Path to your Python executable; in case you work locally on a Windows machine

### database_settings.json

```
{
    "database": {
        "name":"",
        "user":"",
        "password":"",
        "host":"",
        "port":""
    }
}

```

**name** - Name of the database
**user** - User for the database
**password** - Password for the database
**host** - Address the database is on
**port** - Port the database is on
