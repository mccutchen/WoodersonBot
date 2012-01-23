from ext.gaefab import *

def pre_deploy_hook(tag, export):
    """Ensure that the secrets.py file is copied in from a safe place before
    deploying.
    """
    if not os.path.exists('secrets.py'):
        local('scp overloaded.org:woodersonbot/secrets.py .')
    return True

deploy.pre_deploy_hook = pre_deploy_hook
