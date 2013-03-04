def encodeShortStat(files_changed, insertions, deletions):
    parts = []
    if files_changed == 1:
        parts.append('1 file changed')
    else:
        parts.append('%d files changed'%files_changed)
    if insertions > 0:
        parts.append('%d insertions(+)'%insertions)
    if deletions > 0:
        parts.append('%d deletions(-)'%deletions)
    return ', '.join(parts)


