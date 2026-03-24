with open('wadiz_dump.html', encoding='utf-8') as f:
    content = f.read()

import re
# 실제 카드 클래스명 찾기
cards = re.findall(r'class="([^"]*[Rr]eward[^"]*)"', content)
for c in set(cards):
    print(c)