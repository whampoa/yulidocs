# coding:utf-8
import sys
import os
import string

punctuation = string.punctuation.replace("$", "") + "-"
import nltk
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# nltk.download('punkt')
# nltk.download('stopwords')
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

lemmatizer = WordNetLemmatizer()
# nltk.download('wordnet')
from nltk.corpus import stopwords
from nltk.corpus import wordnet as wn

wn.ensure_loaded()
stopwordstest = stopwords.words()
import re


def get_label_name(i):
    if i == 0:
        return 'First_day'
    if i == 1:
        return 'Holiday_Leave'
    if i == 2:
        return 'Remuneration'
    if i == 3:
        return 'Sick_leave'
    if i == 4:
        return 'Termination'
    return 'other'


def get_label(pred):
    import numpy as np
    index = np.argmax(pred[1])
    label = int(pred[0][index][-1])
    return label


def chooseBest(typei, arr):
    first_day = test['data'][test['label'].isin([arr[typei][0]])]
    Firstday = ""
    for i in first_day.index:
        text = first_day[i]
        values = mandatory1_dict[arr[typei][1]]
        for value in values:
            if value in text.lower():
                text = text.strip(" ")
                Firstday += text.replace('\n', '') + ".\n"
                break
    return Firstday


def preprocess(start, end):
    wn.ensure_loaded()
    for i in range(start, end):  # [strat,end)
        if (i + 1 > len(text)):
            return
        sentence = text[i]
        Sentence = ""
        for word in word_tokenize(sentence):
            if not word in stopwordstest:
                Sentence = Sentence + " " + lemmatizer.lemmatize(word.translate(str.maketrans('', '', punctuation)))
        real_test_token.append(Sentence)


def cleantext(t):
    t = t.replace("\n", "")
    t = t.replace("\t", "")
    t = t.replace("\\", "")
    t = t.replace("\"", "")
    return t


def main(args):
    file_path = args[1]
    extensioni = file_path.rfind('.')
    if extensioni == -1:
        exit()
    extention = file_path[extensioni + 1:].lower()
    global text
    text = ''
    if ('docx' in extention):
        import docx2txt
        text = docx2txt.process(file_path)
    if ('pdf' in extention):
        import pdfplumber
        for p in pdfplumber.open(file_path).pages:
            text += p.extract_text()
    if ('jpg' in extention or 'jpeg' in extention or 'png' in extention):
        import easyocr
        reader = easyocr.Reader(['en'])
        print(file_path)
        result = reader.readtext(file_path)
        text = ' '.join([r[1] for r in result])
    text = text.split('.')

    # preprocess multithread
    import threading
    global real_test_token
    real_test_token = []
    textl = len(text)
    width = 20
    for i in range(0, textl // width + 1):
        thread = threading.Thread(target=preprocess, args=(i * width, (i + 1) * width,))  # [strat,end)
        thread.start()
        thread.join()
    # print('tsting')
    # real_test_token=[]
    # for sentence in text:
    #     Sentence=""
    #     for word in word_tokenize(sentence):
    #         if not word in stopwords.words():
    #             Sentence=Sentence+" "+lemmatizer.lemmatize(word.translate(str.maketrans('', '', punctuation)))
    #     print(Sentence)
    #     real_test_token.append(Sentence)

    # Predict 
    import platform
    separator = '\\'
    if (platform.platform().lower().find('win') == -1):
        separator = '/'

    import fasttext
    fasttext.FastText.eprint = lambda x: None
    model_path = "." + separator + 'model' + separator + 'model.bin'
    model = fasttext.load_model(model_path)
    test_label = []
    type_list = []
    for i in range(len(real_test_token)):
        res = model.predict(" ".join(real_test_token[i]), k=2)
        test_label.append(get_label(res))
        type_list.append(get_label_name(get_label(res)))

    global test
    import pandas as pd
    test = pd.DataFrame({'data': text, 'label': type_list})
    test = test.drop(index=(test.loc[(test['label'] == 5)].index))

    # Choose the best result
    global mandatory1_dict
    mandatory1_dict = dict()
    mandatory1_dict['Remuneration'] = ['$', 'aed', 'usd', 'aud', 'Allowance', 'salary', 'basic salary', 'wage',
                                       'remuneration', 'base']
    mandatory1_dict['Sickleave'] = ['sick', 'medical', 'hospital', 'ill']
    mandatory1_dict['Holidayleave'] = ['annual', 'holiday', 'vacation']
    mandatory1_dict['Termination'] = ['terminate', 'end', 'notice']
    mandatory1_dict['First day'] = ['commence', 'start', 'begin']

    # First_day
    first_day = test['data'][test['label'].isin(['First_day'])]
    Firstday = ""
    for i in first_day.index:
        text = first_day[i]
        values = mandatory1_dict['First day']
        for value in values:
            if value in text.lower():
                text = text.strip(" ")
                Firstday += text.replace('\n', '') + ".\n"
                break

    # extract datatime keyword
    import datefinder
    matches = list(datefinder.find_dates(Firstday))
    final_firstday = ""

    if len(matches) > 0:
        for i in range(len(matches)):
            # date returned will be a datetime.datetime object. !!!'Day-Month-Year:08/10/2020' cannot clearly know(However, the documents are not write ambiguously)
            keydate = matches[i]
            final_firstday += str(keydate)
    else:
        final_firstday = "No dates found"

    import re
    # holiday_leave
    holiday_leave = test['data'][test['label'].isin(['Holiday_Leave'])]
    Holidayleave = []
    for i in holiday_leave.index:
        text = holiday_leave[i]
        values = mandatory1_dict['Holidayleave']
        for value in values:
            if value in text.lower():
                text = text.strip(" ")
                Holidayleave.append(text)
                break

    # Judge whether this documents mentioning Holiday Leave
    if len(Holidayleave) == 0:
        holidayleave = "No"
    else:
        holidayleave = "Yes"

    final_holidayleave = []

    for i in range(len(Holidayleave)):
        line = Holidayleave[i]
        matchObj = re.match(r'(.*)(hour|day|week|month)(.*?) .*', line, re.M | re.I | re.S)
        if matchObj:
            a = re.findall(r"[.,\d]+\s*.*?(?:week|day|hour|month?)\s*[.,\d]+|[.,\d]+\s*.*?(?:week|day|hour|month?)",
                           line, re.I)
            if len(a) >= 1:
                h = "Holdiday Leave:" + str(a)
                final_holidayleave.append(h)
    if len(final_holidayleave) == 0:
        final_holidayleave = "Not define the specific time for Holiday leave"

    # sick_leave
    sick_leave = test['data'][test['label'].isin(['Sick_leave'])]
    Sickleave = []
    for i in sick_leave.index:
        text = sick_leave[i]
        values = mandatory1_dict['Sickleave']
        for value in values:
            if value in text.lower():
                text = text.strip(" ")
                Sickleave.append(text)
                break

    final_sickleave = []

    for i in range(len(Sickleave)):
        line = Sickleave[i]
        matchObj = re.match(r'(.*)(hour|day|week)(.*?) .*', line, re.M | re.I | re.S)
        if matchObj:
            a = re.findall(
                r"[.,\d]+\s*(?:week|day|hour?)\s*[.,\d]+|[.,\d]+\s*(?:week|weekdays|paid sick days|day|hour?)", line,
                re.I)
            if len(a) >= 1:
                s = "Sick Leave:" + str(a)
                final_sickleave.append(s)

    if len(Sickleave) == 0:
        sickleave = "No"
        final_sickleave = "Not define the specific time for Sick leave"
    else:
        sickleave = "Yes"
        if len(final_sickleave) == 0:
            final_sickleave = Sickleave[0]

    # remuneration
    import re
    remuneration = test['data'][test['label'].isin(['Remuneration'])]
    Remuneration = ""
    for i in remuneration.index:
        text = remuneration[i]
        values = mandatory1_dict['Remuneration']
        for value in values:
            if value in text.lower():
                text = text.strip(" ")
                Remuneration += text.replace('\n', '') + "\n"
                break

    final_remuneration = []
    for i in remuneration.index:
        line = remuneration[i]
        # basic salary
        matchObj = re.match(r'(.*)(Basic|base|basis|gross)(.*?) .*', line, re.M | re.I | re.S)
        if matchObj:
            a = re.findall(
                r"[£$€]\s*[.,\d]+|[.,\d]+\s*[£$€]|(?:Eur|AUD|dollars?)\s*[.,\d]+|[.,\d]+\s*(?:Eur|AUD|dollars?)", line,
                re.I)
            if len(a) >= 1:
                s1 = "Basic salary:" + str(a)
                final_remuneration.append(s1)

        # Accommodation
        matchObj = re.match(r'(.*) Accommodation(.*?) .*', line, re.M | re.I | re.S)
        if matchObj:
            b = re.findall(
                r"[£$€]\s*[.,\d]+|[.,\d]+\s*[£$€]|(?:Eur|AUD|dollars?)\s*[.,\d]+|[.,\d]+\s*(?:Eur|AUD|dollars?)", line,
                re.I)
            if len(b) >= 1:
                s2 = "Accommodation:" + str(b)
                final_remuneration.append(s2)

        # Transportation
        matchObj = re.match(r'(.*)(Transport|transportation) (.*?) .*', line, re.M | re.I | re.S)
        if matchObj:
            c = re.findall(
                r"[£$€]\s*[.,\d]+|[.,\d]+\s*[£$€]|(?:Eur|AUD|dollars?)\s*[.,\d]+|[.,\d]+\s*(?:Eur|AUD|dollars?)", line,
                re.I)
            if len(c) >= 1:
                s3 = "Transportation:" + str(c)
                final_remuneration.append(s3)

        # Allowance
        matchObj = re.match(r'(.*) Allowance (.*?) .*', line, re.M | re.I | re.S)
        if matchObj:
            d = re.findall(
                r"[£$€]\s*[.,\d]+|[.,\d]+\s*[£$€]|(?:Eur|AUD|dollars?)\s*[.,\d]+|[.,\d]+\s*(?:Eur|AUD|dollars?)", line,
                re.I)
            if len(d) >= 1:
                s4 = "Allowance:" + str(d)
                final_remuneration.append(s4)

        # insurance
        matchObj = re.match(r'(.*) insurance (.*?) .*', line, re.M | re.I | re.S)
        if matchObj:
            e = re.findall(
                r"[£$€]\s*[.,\d]+|[.,\d]+\s*[£$€]|(?:Eur|AUD|dollars?)\s*[.,\d]+|[.,\d]+\s*(?:Eur|AUD|dollars?)", line,
                re.I)
            if len(e) >= 1:
                s5 = "Insurance Benefits:" + str(e)
                final_remuneration.append(s5)

        matchObj = re.match(r'(.*) total (.*?) .*', line, re.M | re.I | re.S)
        if matchObj:
            f = re.findall(
                r"[£$€]\s*[.,\d]+|[.,\d]+\s*[£$€]|(?:Eur|AUD|dollars?)\s*[.,\d]+|[.,\d]+\s*(?:Eur|AUD|dollars?)", line,
                re.I)
            if len(f) >= 1:
                s6 = "Total:" + str(f)
                final_remuneration.append(s6)

                # termination
    termination = test['data'][test['label'].isin(['Termination'])]
    Termination = []
    for i in termination.index:
        text = termination[i]
        values = mandatory1_dict['Termination']
        for value in values:
            if value in text.lower():
                text = text.strip(" ")
                Termination.append(text)
                break

    # optimizing ‘termination’ result； only extract notice information
    Termination1 = []
    Termination2 = ""
    for i in range(len(Termination)):
        text = Termination[i]
        values = ['notice']
        for value in values:
            if value in text.lower():
                text = text.strip(" ")
                Termination1.append(text)
                Termination2 += text.replace('\n', ' ') + ". \n"
                break

    final_termination = ""
    for i in range(len(Termination)):
        text = Termination[i]

        infos1 = ['no notice', 'without']
        for info in infos1:
            if info in text.lower():
                ter1 = 'Without notice: '
                details = ['probation', 'introductory', 'months']
                txt = text.split()
                for detail in details:
                    for i in range(len(txt)):
                        if detail in txt[i]:
                            key = txt[i - 1] + ' ' + txt[i]
                            ter1 += key + "; "
                            break
                break

        infos2 = ['1 week', 'one week', 'one （1） week', '7 days', 'seven days', 'seven (7) days']
        for info in infos2:
            if info in text.lower():
                ter2 = "1 week notice: "
                details = ['month', 'year', 'period', 'probation']
                txt = text.split()
                for detail in details:
                    for i in range(len(txt)):
                        if detail in txt[i]:
                            key = txt[i - 1] + ' ' + txt[i]
                            ter2 += key + "; "
                            break
                break

        infos3 = ['15 days', 'fifteen (15) days', 'fifteen days', '2 weeks', 'two week', 'two (2) week', '14 days',
                  'forty day', 'forty (14) day']
        for info in infos3:
            if info in text.lower():
                ter3 = "15 days notice: "
                details = ['month', 'year', 'period', 'probation']
                txt = text.split()
                for detail in details:
                    for i in range(len(txt)):
                        if detail in txt[i]:
                            key = txt[i - 1] + ' ' + txt[i]
                            ter3 += key + "; "
                            break
                break

        infos4 = ['thirty (30) days', '30 day', 'thirty day', '1 month', 'one month', 'four weeks', 'four (4) weeks',
                  '4 weeks', 'one (1) month']
        for info in infos4:
            if info in text.lower():
                details = ['month', 'year', 'period', 'probation']
                ter4 = "1 month notice: "
                txt = text.split()
                for detail in details:
                    for i in range(len(txt)):
                        if detail in txt[i]:
                            key = txt[i - 1] + ' ' + txt[i]
                            ter4 += key + "; "
                            break
                break

    # for a sentence don't have related information
    y1 = 'ter1' in locals().keys()
    if y1 == False:
        ter1 = "Without notice: Not mention"
    y2 = 'ter2' in locals().keys()
    if y2 == False:
        ter2 = "1 week notice: Not mention"
    y3 = 'ter3' in locals().keys()
    if y3 == False:
        ter3 = "15 days notice: Not mention"
    y4 = 'ter4' in locals().keys()
    if y4 == False:
        ter4 = "1 month notice: Not mention"

        # for a sentence has Related information, but don't have condition content.
    if 1 <= len(ter1.split()) <= 2:
        ter1 = "Without notice: Yes"
    if 2 <= len(ter2.split()) <= 3:
        ter2 = "1 week notice: Yes"
    if 2 <= len(ter3.split()) <= 3:
        ter3 = "15 days notice: Yes"
    if 2 <= len(ter4.split()) <= 3:
        ter4 = "1 month notice: Yes"
    final_termination = ter1 + "<br>" + ter2 + "<br>" + ter3 + "<br>" + ter4
    # print(final_termination)

    nullstr = '-'
    results = []
    results.append([nullstr, final_firstday])
    results.append([holidayleave, final_holidayleave])
    results.append([nullstr, final_remuneration])
    results.append([sickleave, final_sickleave])
    results.append([nullstr, final_termination])

    res = ''
    for j in range(0, 5):
        result = results[j]
        for i in range(len(result)):
            if (type(result[i]) == type('')):
                result[i] = cleantext(result[i])
                if (result[i] == ""):
                    result[i] = nullstr
            else:
                if (len(result[i]) == 0):
                    result[i] = nullstr
                    continue
                for t in range(len(result[i])):
                    result[i][t] = cleantext(result[i][t])

        if (type(result[1]) == type('')):
            res = res + "{\"status\":\"" + str(result[0]) + "\",\"label\":\"" + str(j) + "\",\"data\":\"" + str(
                result[1]) + "\"}\n"

        else:
            if (len(result[1]) > 0):
                r = '{"data":['
                for k in range(len(result[1])):
                    if k == len(result[1]) - 1:
                        r = r + '"' + result[1][k] + '"'
                    else:
                        r = r + '"' + result[1][k] + '",'
                r = r + '],"label":"' + str(j) + '","status":"' + result[0] + '"}\n'
                res = res + r
            else:
                res = res + '{"status":"' + result[0] + '","label":"' + str(j) + '","data":"' + nullstr + '"}\n'
    return res


if __name__ == "__main__":
    print(main(sys.argv))
