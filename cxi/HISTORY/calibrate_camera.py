def calibrate_camera(positions):
    '''
    Calibrates the camera, returning cam_roll and pxsize
    '''
    from cam_utils import get_cam_roll_pxsize
    
    imgs = []
    impos = []
    for pos in positions:
        #move motor to pos
        #wait until motor has moved
        #im = Questar raw image
        #imgs.append(im)
        #impos.append(current position)
        pass
    
    cam_roll, pxsize = get_cam_roll_pxsize(imgs, impos)
    return cam_roll, pxsize
