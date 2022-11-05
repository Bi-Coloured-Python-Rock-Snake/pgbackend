from greenlet import greenlet


# get var from sync code
def getvar():
    other_g = greenlet.getcurrent().other_greenlet.getvar()