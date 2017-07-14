# from posixpath import join
# from datetime import datetime
#
# from fabric.operations import local as lrun, run, prompt
# from fabric.api import cd, env, prefix, sudo, settings, reboot as restart_sys
# from fabric.contrib.files import append
# from fabric.utils import fastprint
# from fabric.context_managers import hide
#
# import os
# import random
# import string
#
# # Config for local system
# def localhost():
#     env.user = 'django'
#     env.run = lrun
#     env.hosts = ['localhost']
#
# # Config for remote system
# def remote():
#     env.user = 'django'
#     env.run = run
#     env.hosts = ['192.168.2.48:25000']
#     env.key_filename=['~/.ssh/id_rsa.pub']
#
# PROJECT_NAME = 'myproject'
# HOME_DIR = '/home/django'
# BASE_DIR = join(HOME_DIR, 'myproject')
#
# NGINX_CONFIG = '/etc/nginx'
# SYSTEMD_CONFIG = '/etc/systemd/system'
# FAIL2_CONFIG = '/etc/fail2ban/'
#
# DATABASE_USER = 'myprojectuser'
# DATABASE_PASSWORD = 'randomtemppassword'
#
# ORIGIN_DIR = "https://github.com/LazerCube/django_quickstart_fabric.git"
#
# def print_status(description):
#     def print_status_decorator(fn):
#         def print_status_wrapper():
#             now = datetime.now().strftime('%H:%M:%S')
#             fastprint('({time}) {description}{suffix}'.format(
#                 time=now,
#                 description=description.capitalize(),
#                 suffix='...\n')
#             )
#             fn()
#             now = datetime.now().strftime('%H:%M:%S')
#             fastprint('({time}) {description}{suffix}'.format(
#                 time=now,
#                 description='...finished '+description,
#                 suffix='.\n')
#             )
#         return print_status_wrapper
#     return print_status_decorator
#
# @print_status('upgrading system')
# def upgrade_system():
#     sudo('apt-get update -y')
#     sudo('apt-get upgrade -y')
#
# @print_status('installing software')
# def install_software():
#     sudo('apt-get install -y git nginx python-dev python-pip libpq-dev postgresql postgresql-contrib fail2ban sendmail iptables-persistent')
#     sudo('pip install --upgrade pip')
#     sudo('pip install -U virtualenvwrapper')
#     append(join(HOME_DIR, '.bash_profile'), ('export WORKON_HOME={0}/.virtualenvs'.format(HOME_DIR), 'source /usr/local/bin/virtualenvwrapper.sh'))
#
# @print_status('removing software')
# def remove_software():
#     run('rm -rf {0}'.format(join(HOME_DIR, '.bash_profile')))
#     sudo('pip uninstall virtualenvwrapper')
#     sudo('apt-get purge -y git nginx python-dev python-pip libpq-dev postgresql postgresql-contrib fail2ban sendmail iptables-persistent')
#     sudo('apt-get autoremove')
#
# @print_status('creating database')
# def create_database():
#     sudo('psql -c "CREATE DATABASE %s;"' % (PROJECT_NAME), user='postgres')
#     sudo('psql -c "CREATE USER %s WITH PASSWORD \'%s\';"' % (DATABASE_USER, DATABASE_PASSWORD), user='postgres')
#     sudo('psql -c "ALTER ROLE %s SET client_encoding TO \'utf8\';"' % (DATABASE_USER), user='postgres')
#     sudo('psql -c "ALTER ROLE %s SET default_transaction_isolation TO \'read committed\';"' % (DATABASE_USER), user='postgres')
#     sudo('psql -c "ALTER ROLE %s SET timezone TO \'UTC\';"' % (DATABASE_USER), user='postgres')
#     sudo('psql -c "GRANT ALL PRIVILEGES ON DATABASE %s TO %s;"' % (PROJECT_NAME, DATABASE_USER), user='postgres')
#
# def install_myproject(origin=ORIGIN_DIR):
#     run('git clone -b master {0} {1}'.format(origin, BASE_DIR))
#     run('mkdir {0}'.format(join(BASE_DIR, 'logs')))
#
# @print_status('upgrading project')
# def upgrade_myproject():
#     with cd(BASE_DIR):
#         run('git pull origin master')
#
# @print_status('removing project')
# def remove_myproject():
#     run('rm -rf {0}'.format(BASE_DIR))
#
# @print_status('creating virtual environment')
# def create_virtualenv():
#     run('mkvirtualenv %s' %(PROJECT_NAME))
#
# @print_status('removing virtual environment')
# def remove_virtualenv():
#     run('rmvirtualenv %s' %(PROJECT_NAME))
#
# @print_status('deploying requirements')
# def deploy_requirements():
#     with prefix('workon %s' %(PROJECT_NAME)):
#         run('pip install -r {0}'.format(join(BASE_DIR,'requirements/production.txt')))
#
# @print_status('deploying gunicorn service')
# def deploy_gunicorn(settings=None):
#     sudo('rm -rf {0}'.format(join(SYSTEMD_CONFIG, 'gunicorn.service')))
#     sudo('cp -f {0} {1}'.format(join(BASE_DIR, 'bin/gunicorn.service'), join(SYSTEMD_CONFIG, 'gunicorn.service')))
#     if settings:
#         append(join(HOME_DIR, '.bash_profile'), 'export DJANGO_SETTINGS_MODULE=\'config.settings.{0}\''.format(settings))
#     with prefix('workon %s' %(PROJECT_NAME)):
#         make_migrations()
#         migrate_models()
#         collect_static()
#         sudo('systemctl start gunicorn')
#         sudo('systemctl enable gunicorn')
#
# @print_status('making migrations')
# def make_migrations():
#     run('python {0} {1}'.format(join(BASE_DIR, 'project/manage.py'), 'makemigrations'))
#
# @print_status('migrating models')
# def migrate_models():
#     run('python {0} {1}'.format(join(BASE_DIR, 'project/manage.py'), 'migrate'))
#
# @print_status('collecting static files')
# def collect_static():
#     run('python {0} {1}'.format(join(BASE_DIR, 'project/manage.py'), 'migrate'))
#
# @print_status('deploying nginx')
# def deploy_nginx():
#     sudo('rm -rf {0}'.format(join(NGINX_CONFIG, ('sites-available/%s' %(PROJECT_NAME)))))
#     sudo('rm -rf {0}'.format(join(NGINX_CONFIG, 'sites-enabled/default')))
#     sudo('cp -f {0} {1}'.format(join(BASE_DIR, 'config/nginx.conf'), join(NGINX_CONFIG, ('sites-available/%s' %(PROJECT_NAME)))))
#     with settings(warn_only=True):
#         sudo('ln -s /etc/nginx/sites-available/%s /etc/nginx/sites-enabled' %(PROJECT_NAME))
#     sudo('nginx -t')
#     sudo('systemctl restart nginx')
#
# @print_status('deploying fail2ban')
# def deploy_fail2ban():
#     sudo('ufw disable')
#     sudo('rm -rf {0}'.format(join(FAIL2_CONFIG, 'jail.local')))
#     sudo('cp -f {0} {1}'.format(join(BASE_DIR, 'config/jail.conf'), join(FAIL2_CONFIG, 'jail.local')))
#
# @print_status('deploying iptables')
# def deploy_iptables():
#     sudo('systemctl stop fail2ban')
#     # Doesn't seem to work in ubuntu server 16.04
#     # sudo('iptables-persistent flush')
#     sudo('netfilter-persistent flush')
#     sudo('iptables -A INPUT -i lo -j ACCEPT')
#     sudo('iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT')
#     sudo('iptables -A INPUT -p tcp --dport 25000 -j ACCEPT')
#     sudo('iptables -A INPUT -p tcp -m multiport --dports 80,443 -j ACCEPT')
#     sudo('iptables -A INPUT -j DROP')
#     sudo('dpkg-reconfigure iptables-persistent')
#     sudo('systemctl start fail2ban')
#
# def generate_key(secret_key=None):
#     if secret_key:
#         return secret_key
#     secret_key = ("".join([random.SystemRandom().choice(string.digits + string.letters + string.punctuation) for i in range(100)]))
#     return secret_key
#
# def create_key(secret_key=None):
#     remove_key()
#     append("/etc/secret_key.txt", "{0}".format(generate_key(secret_key)), use_sudo=True)
#
# def remove_key():
#     sudo('rm -rf /etc/secret_key')
#
# def sys_reboot(reboot=False):
#     if reboot:
#         with settings(warn_only=True):
#             print('::Rebooting to apply new changes...')
#             restart_sys(200)
#             print('::Continuing with fabric...')
#
# @print_status('starting services')
# def start():
#     sudo("systemctl start fail2ban")
#     sudo("systemctl start gunicorn")
#     sudo("systemctl start nginx")
#
# @print_status('stopping services')
# def stop():
#     sudo("systemctl stop nginx")
#     sudo("systemctl stop gunicorn")
#     sudo("systemctl stop fail2ban")
#
# @print_status('restarting services')
# def restart():
#     sudo("systemctl restart gunicorn")
#     sudo("systemctl restart nginx")
#     sudo('systemctl stop fail2ban')
#     sudo("systemctl start fail2ban")
#
# def manage(command=''):
#     with prefix('workon %s' %(PROJECT_NAME)):
#         run('python {0} {1}'.format(join(BASE_DIR, 'project/manage.py'), command))
#
# def help():
#     message = '''
#     Remote updating application with fabric.
#
#     Usage example:
#
#     Perform a full_install of project on remote server:
#     fab remote full_install
#
#     '''
#     fastprint(message)
#
# def full_install(origin=ORIGIN_DIR, settings=None, secret_key=None, reboot=False):
#     if not(settings):
#         settings = prompt("When installing for the first time you must define a django config file to use.")
#         # Check if config file exists before continuing
#     with hide('stderr', 'stdout', 'warnings', 'running'):
#         upgrade_system()
#         install_software()
#         sys_reboot(reboot)
#         create_database()
#         install_myproject(origin)
#         create_key(secret_key)
#         create_virtualenv()
#         deploy_requirements()
#         deploy_fail2ban()
#         deploy_gunicorn(settings)
#         deploy_nginx()
#         deploy_iptables()
#         start()
#
# def quick_upgrade(settings=None, secret_key=None):
#     upgrade_myproject()
#     create_key(secret_key)
#     deploy_requirements()
#     deploy_fail2ban()
#     deploy_gunicorn(settings)
#     restart()
#
# def full_upgrade(settings=None, secret_key=None, reboot=False):
#     upgrade_system()
#     install_software()
#     sys_reboot(reboot)
#     upgrade_myproject()
#     create_key(secret_key)
#     deploy_requirements()
#     deploy_fail2ban()
#     deploy_gunicorn(settings)
#     deploy_nginx()
#     deploy_iptables()
#     restart()
#
# def full_remove(reboot=False):
#     stop()
#     remove_virtualenv()
#     remove_key()
#     remove_myproject()
#     remove_software()
#     reboot(reboot)

import json
from datetime import datetime

from fabric.api import *
from fabric.operations import require
from fabric.context_managers import settings
from fabric.utils import fastprint

from fabvenv import virtualenv
from unipath import Path

SETTINGS_FILE_PATH = Path(__file__).ancestor(1).child('project_settings.json')

with open(SETTINGS_FILE_PATH, 'r') as f:
    # Load settings.
    project_settings = json.loads(f.read())

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
    def deploy(tests='yes'):
        '''
        Deploys project to previously set stage.
        '''
        require('stage', provided_by=(stable, development))
        require('settings', provided_by=(stable, development))
        # Set env.
        env.vcs_type = project_settings['vcs_type']
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

def pull_repository():
    '''
    Updates local repository, selecting the vcs from configuration file.
    '''
    if env.vcs_type == 'mercurial':
        pull_mercurial_repository
    elif env.vcs_type == 'git':
        pull_git_repository
    else:
        abort(
            'vcs type must be either mercurial or git,'
            ' currently is: {vcs}'.format(vcs=env.vcs_type)
        )

@print_status('pulling mercurial repository')
def pull_mercurial_repository():
    run('hg pull -u')
    run('hg up {branch}'.format(branch=env.settings['vcs_branch']))

@print_status('pulling git repository')
def pull_git_repository():
    command = 'git pull {} {}'.format(
        env.project_settings.get('git_repository'),
        env.settings.get('vcs_branch')
    )
    run(command)

@print_status('collecting static files')
def collect_static():
    run('python manage.py collectstatic')

@print_status('installing requirements')
def install_requirements():
    with cd(env.settings['code_src_directory']):
        run('pip install -r {0}'.format(env.settings['requirements_file']))

@print_status('migrating models')
def migrate_models():
    run('python manage.py migrate')

@print_status('restarting application')
def restart_application():
    with settings(warn_only=True):
        restart_command = env.settings['restart_command']
        result = run(restart_command)
    if result.failed:
        abort('Could not restart application.')
