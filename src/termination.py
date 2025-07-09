import os

def get_termination_flag_path( flag_path,news_id ):
    return flag_path + '/distnewsearchfound'  + str(news_id) 

def check_termination_flag(flag_path, news_id ):
    """Check if termination flag exists"""
    return os.path.exists(get_termination_flag_path( flag_path,news_id ))

def set_termination_flag():
    """Create termination flag atomically"""
    try:
        with open(get_termination_flag_path( flag_path,news_id ), "w") as f:
            f.write("1")
        return True
    except:
        return False

