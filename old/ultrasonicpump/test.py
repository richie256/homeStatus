def update(x):
    """
    'mdi:circle-outline'
    'mdi:circle-slice-1'
    'mdi:circle-slice-2'
    'mdi:circle-slice-3'
    'mdi:circle-slice-4'
    'mdi:circle-slice-5'
    'mdi:circle-slice-6'
    'mdi:circle-slice-7'
    'mdi:circle-slice-8'
    'mdi:alert-circle'
    """
    if x is None:
        return 'mdi:circle-outline'
    else:
        perc = int(round((x / 10) - .01)) * 10
    
    if x >= 90:
        icon = 'mdi:alert-circle'
    elif x < 10:
        icon = 'mdi:circle-outline'
    else:
        # icon = x
        # icon = (perc/10)
        icon = 'mdi:circle-slice'
        icon += '-{}'.format(perc / 10)
    
    return icon 


for x in range(100):
    print str(x+1) + " "  + str(update(x+1))
    # print update(x)
