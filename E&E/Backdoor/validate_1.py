num = 'Ftdru'


def validate(string):
    temp = bytearray()
    answers = []
    for i in range(2, 100):
        try:
            temp = bytearray()
            for j in range(len(num)):
                temp.append(i ^ ord(num[j]))
            ans = temp.decode('utf-8')
            if all(32 <= ord(c) <= 126 for c in ans):
                answers.append(ans)
        except UnicodeDecodeError:
            pass
    if string in answers:
        return True