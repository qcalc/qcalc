
from qcore.mod_anno import qfl


def demo_addy__info():
    return {
        'title': 'Add from 2nd Package',
        # 'onsubmit': 'alert("hello "+_cid)'
    }


def demo_addy(x: qfl = 1, y=2):
    """ Add two values x and y
    parameters:
    :param x:
    :param y:
    :return:
    """
    return x + y

