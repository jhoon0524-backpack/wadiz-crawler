with open('wadiz_dump.html', encoding='utf-8') as f:
    content = f.read()

idx = content.find('LabelBadge_red')
print(repr(content[idx:idx+300]))