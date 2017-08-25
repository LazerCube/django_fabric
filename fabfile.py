import json
import string
import random
from datetime import datetime
from posixpath import join

from fabric.api import *
from fabric.operations import require
from fabric.context_managers import settings
from fabric.contrib.files import append
from fabric.utils import fastprint

from fabvenv import virtualenv
from unipath import Path

PROJECT_SETTINGS_FILE_PATH = Path(__file__).ancestor(1).child('project_settings.json')
DATABASE_SETTINGS_FILE_PATH = Path(__file__).ancestor(1).child('database_settings.json')

with open(PROJECT_SETTINGS_FILE_PATH, 'r') as f:
    # Load project settings.
    project_settings = json.loads(f.read())

with open(DATABASE_SETTINGS_FILE_PATH, 'r') as f:
    # Load database settings.
    database_settings = json.loads(f.read())

env.prompts = {
    'Type \'yes\' to continue, or \'no\' to cancel: ': 'yes'
}

def set_stage(stage_name='development'):
    stages = project_settings['stages'].keys()
    if stage_name not in stages:
        raise KeyError('Stage name "{0}" is not a valid stage ({1})'.format(
        ','.join(stages))
        )
    env.stage = stage_name

@task
def stable():
    set_stage('stable')
    set_project_settings()

@task
def development():
    set_stage('development')
    set_project_settings()

def set_project_settings():
    stage_settings = project_settings['stages'][env.stage]
    if not all(project_settings.itervalues()):
        raise KeyError('Missing values in project settings.')
    env.settings = stage_settings

@task
def install():
    '''
    Installs project to previously set stage.
    '''
    require('stage', provided_by=(stable, development))
    require('settings', provided_by=(stable, development))
    # Set env.
    env.user = env.settings['user']
    env.host_string = env.settings['host']

    # upgrade_system()
    install_software()
    with hide('stderr', 'stdout', 'warnings', 'running'):
        clone_repository()
        create_virtualenv()
        with virtualenv(env.settings['venv_directory']):
            with cd(env.settings['code_src_directory']):
                install_requirements()
                create_key()
                create_database()
                deploy_gunicorn()
                make_migrations()
                migrate_models()
                collect_static()
            deploy_fail2ban()
            deploy_nginx()
            deploy_iptables()
        restart()
    #restart_application()

@task
def deploy(tests='yes'):
    '''
    Deploys project to previously set stage.
    '''
    require('stage', provided_by=(stable, development))
    require('settings', provided_by=(stable, development))
    # Set env.
    env.user = env.settings['user']
    env.host_string = env.settings['host']

    with hide('stderr', 'stdout', 'warnings', 'running'):
        if tests == 'yes':
            with lcd(project_settings['local']['code_src_directory']):
                run_tests()
        with cd(env.settings['code_src_directory']):
            pull_repository()
        with virtualenv(env.settings['venv_directory']):
            with cd(env.settings['code_src_directory']):
                collect_static()
                install_requirements()
                migrate_models()
        restart_application()

def print_status(description):
    def print_status_decorator(fn):
        def print_status_wrapper():
            now = datetime.now().strftime('%H:%M:%S')
            fastprint('({time}) {description}{suffix}'.format(
                time=now,
                description=description.capitalize(),
                suffix='...\n')
            )
            fn()
            now = datetime.now().strftime('%H:%M:%S')
            fastprint('({time}) {description}{suffix}'.format(
                time=now,
                description='...finished '+description,
                suffix='.\n')
            )
        return print_status_wrapper
    return print_status_decorator

@print_status('upgrading system')
def upgrade_system():
    sudo('apt-get update -y')
    sudo('apt-get upgrade -y')

@print_status('installing software')
def install_software():
    sudo('apt-get install -y python-pip')
    run('pip install --upgrade pip')
    sudo('pip install -U virtualenvwrapper')
    sudo('apt-get install -y git iptables-persistent nginx libpq-dev postgresql postgresql-contrib fail2ban sendmail')
    append(('/home/{0}/.bash_profile'.format(env.user)), ('export WORKON_HOME=/home/{0}/.virtualenvs'.format(env.user), 'source /usr/local/bin/virtualenvwrapper.sh'))

@print_status('removing software')
def remove_software():
    run('rm -rf {0}'.format('.bash_profile'))
    sudo('pip uninstall virtualenvwrapper')
    sudo('apt-get purge -y git nginx python-dev python-pip libpq-dev postgresql postgresql-contrib fail2ban sendmail iptables-persistent')
    sudo('apt-get autoremove')

@print_status('creating virtual environment')
def create_virtualenv():
    run('mkvirtualenv %s' %(project_settings['project_name']))

@print_status('removing virtual environment')
def remove_virtualenv():
    run('rmvirtualenv %s' %(project_settings['project_name']))

@print_status('running tests locally')
def run_tests():
    '''
    Runs all tests locally. Tries to use settings.test first for sqlite db.
    To avoid running test, use `deploy:tests=no`.
    '''
    python_exec = project_settings['local']['venv_python_executable']
    test_command = python_exec + ' manage.py test'
    with settings(warn_only=True):
        result = local(test_command + ' --settings=config.settings.local')
        if not result.failed:
            return
    result = local(test_command + ' --settings=config.settings.staging')
    if result.failed:
        abort('Tests failed. Use deploy:tests=no to omit tests.')

@print_status('pulling git repository')
def pull_repository():
    command = 'git pull {} {}'.format(
        env.project_settings.get('git_repository'),
        env.settings.get('vcs_branch')
    )
    run(command)

def clone_repository():
    command = 'git clone -b {} --single-branch {}'.format(
        env.settings['vcs_branch'],
        project_settings['git_repository'],
    )
    run(command)
    # run('mkdir {0}'.format('/home/{0}/logs'.format(env.user)))

@print_status('collecting static files')
def collect_static():
    run('python manage.py collectstatic')

@print_status('installing requirements')
def install_requirements():
    run('pip install -r {0}'.format(env.settings['requirements_file']))

@print_status('making migrations')
def make_migrations():
    run('python manage.py makemigrations')

@print_status('migrating models')
def migrate_models():
    run('python manage.py migrate')

@print_status('creating database')
def create_database():
    sudo('psql -c "CREATE DATABASE %s;"' % (database_settings['database']['name']), user='postgres')
    sudo('psql -c "CREATE USER %s WITH PASSWORD \'%s\';"' % ((database_settings['database']['user']), (database_settings['database']['password'])), user='postgres')
    sudo('psql -c "ALTER ROLE %s SET client_encoding TO \'utf8\';"' % (database_settings['database']['user']), user='postgres')
    sudo('psql -c "ALTER ROLE %s SET default_transaction_isolation TO \'read committed\';"' % (database_settings['database']['user']), user='postgres')
    sudo('psql -c "ALTER ROLE %s SET timezone TO \'UTC\';"' % (database_settings['database']['user']), user='postgres')
    sudo('psql -c "GRANT ALL PRIVILEGES ON DATABASE %s TO %s;"' % ((database_settings['database']['name']), (database_settings['database']['user'])), user='postgres')

def create_key():
    remove_key()
    append("/etc/secret_key.txt", "{0}".format(generate_key()), use_sudo=True)

def generate_key():
    secret_key = ("".join([random.SystemRandom().choice(string.digits + string.letters + string.punctuation) for i in range(100)]))
    return secret_key

def remove_key():
    sudo('rm -rf /etc/secret_key')

@print_status('deploying nginx')
def deploy_nginx():
    config_directory = project_settings['configs']['nginx']['config_directory']
    config_src = project_settings['configs']['nginx']['config_src']
    sudo('rm -rf {0}'.format(join(config_directory, ('sites-available/%s' %(project_settings['project_name'])))))
    sudo('rm -rf {0}'.format(join(config_directory, 'sites-enabled/default')))
    sudo('cp -f {0} {1}'.format(config_src, join(config_directory, ('sites-available/%s' %(project_settings['project_name'])))))
    with settings(warn_only=True):
        sudo('ln -s /etc/nginx/sites-available/%s /etc/nginx/sites-enabled' %(project_settings['project_name']))
    sudo('nginx -t')
    sudo('systemctl restart nginx')

@print_status('deploying fail2ban')
def deploy_fail2ban():
    config_directory = project_settings['configs']['fail2ban']['config_directory']
    config_src = project_settings['configs']['fail2ban']['config_src']
    sudo('ufw disable')
    sudo('rm -rf {0}'.format(join(config_directory, 'jail.local')))
    sudo('cp -f {0} {1}'.format(config_src, config_directory))

@print_status('deploying gunicorn service')
def deploy_gunicorn():
    config_directory = project_settings['configs']['gunicorn']['config_directory']
    config_src = project_settings['configs']['gunicorn']['config_src']
    sudo('rm -rf {0}'.format(join(config_directory, 'gunicorn.service')))
    sudo('cp -f {0} {1}'.format(config_src, join(config_directory, 'gunicorn.service')))
    if settings:
        # append('.bash_profile', 'export DJANGO_SETTINGS_MODULE=\'config.settings.{0}\''.format(settings))
         append('.bash_profile', 'export DJANGO_SETTINGS_MODULE=\'config.settings.production\'')
    sudo('systemctl start gunicorn')
    sudo('systemctl enable gunicorn')

@print_status('deploying iptables')
def deploy_iptables():
    sudo('systemctl stop fail2ban')
    # Doesn't seem to work in ubuntu server 16.04
    # sudo('iptables-persistent flush')
    sudo('netfilter-persistent flush')
    sudo('iptables -A INPUT -i lo -j ACCEPT')
    sudo('iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT')
    sudo('iptables -A INPUT -p tcp --dport 25000 -j ACCEPT')
    sudo('iptables -A INPUT -p tcp -m multiport --dports 80,443 -j ACCEPT')
    sudo('iptables -A INPUT -j DROP')
    sudo('dpkg-reconfigure iptables-persistent')
    sudo('systemctl start fail2ban')

@print_status('starting services')
def start():
    sudo("systemctl start fail2ban")
    sudo("systemctl start gunicorn")
    sudo("systemctl start nginx")

@print_status('stopping services')
def stop():
    sudo("systemctl stop nginx")
    sudo("systemctl stop gunicorn")
    sudo("systemctl stop fail2ban")

@print_status('restarting services')
def restart():
    sudo("systemctl restart gunicorn")
    sudo("systemctl restart nginx")
    sudo('systemctl stop fail2ban')
    sudo("systemctl start fail2ban")

@print_status('restarting application')
def restart_application():
    with settings(warn_only=True):
        restart_command = env.settings['restart_command']
        result = run(restart_command)
    if result.failed:
        abort('Could not restart application.')
