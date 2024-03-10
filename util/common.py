
def validateIP(maybe_ip):
    if not isinstance(maybe_ip, str):
        raise Exception('ip not a string: %s' % maybe_ip)
    parts = maybe_ip.split('.')
    if len(parts) != 4:
        raise Exception('ip not a dotted quad: %s' % maybe_ip)
    for num_s in parts:
        try:
            num = int(num_s)
        except ValueError:
            raise Exception(
                'ip dotted-quad components not all integers: %s' % maybe_ip)
        if num < 0 or num > 255:
            raise Exception(
                'ip dotted-quad component not between 0 and 255: %s' % maybe_ip)
