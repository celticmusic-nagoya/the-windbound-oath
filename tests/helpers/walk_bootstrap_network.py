"""Only the proven, unused HTML Raider still cancelled by startup retargeting."""
def expected_retarget(event, original_url, replacement):
    return (event.get('url') == original_url
            and event.get('failure') == 'net::ERR_ABORTED'
            and event.get('resource_type') == 'image'
            and event.get('before_dev') is True
            and replacement.get('loaded') is True
            and replacement.get('url') != original_url
            and replacement.get('url') in replacement.get('registered', []))
