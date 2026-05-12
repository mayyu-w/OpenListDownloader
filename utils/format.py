# @author: awen


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    index = 0
    size = float(size_bytes)
    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1
    if index == 0:
        return f"{int(size)} B"
    return f"{size:.2f} {units[index]}"


def format_eta(seconds: int) -> str:
    if seconds <= 0:
        return ""
    if seconds < 60:
        return f"{seconds}秒"
    if seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m}分{s}秒"
    h, remainder = divmod(seconds, 3600)
    m, _ = divmod(remainder, 60)
    return f"{h}时{m}分"
