import streamlit as st
import numpy as np
from main import *
from streamlit_option_menu import option_menu
from itertools import compress
from io import BytesIO
from pyxlsb import open_workbook as open_xlsb
import nltk
import simplemma as splm
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise  import cosine_similarity

st.set_page_config(page_title="Universties Senegal",layout="wide")

def make_clickable(link):
    try:
        text = link.split('https://www.au-senegal.com/')[1]
    except:
        try:
            text = link.split('www.')[1]
        except:
            text = link.split('//')[1]
    return f'<a target="_blank" href="{link}">{text}</a>'

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'})
    worksheet.set_column('A:A', None, format1)
    writer.save()
    processed_data = output.getvalue()
    return processed_data



def main():
    st.write("""
            # Orientation SN

            ## Application for universities in Senegal with automatic keyword selection/indexing, using ***Python*** and ***Pandas Library***
            project files : https://github.com/abd2re/abd2re-university-sn-dataframe""")



    st.write("""Data cleansing done with jupyter and excel (pandas excel module)""")

    st.write("""University list from: https://infoetudes.com/liste-adresses-et-contacts-des-universites-ecoles-de-formations-et-instituts-du-senegal/""")

    st.write("""The keyword selection has been done by the code algorithm""")

    st.write("""# Filterable dataframe""")

    st.write("""***keywords auto-selected by frequency***""")
    arr = ''
    for i in keyword_dict:
        arr = arr + ' ' + i + ','
    st.write('['+arr[1:-1]+']')

    val = st.selectbox('Choose',keyword_dict.items())
    kw = val[0]
    unis_filt = unis.copy()
    line = 0

    for i in unis_filt['keywords']:
        for word in i:
            if word == kw:
                break
        else:
            unis_filt.drop(line,axis=0,inplace=True)

        line += 1

    try:
        unis_filt = unis_filt.set_index(np.arange(1,val[1]+1))
    except:
        unis_filt = unis_filt.set_index(np.arange(1,val[1]))


    st.write("""### {} ({})""".format(kw,val[1]))
    col1, col2, col3, col4, col5, space = st.columns([0.5,1,1,1,1,16-5])
    with col1:
        st.write("""Hide:""")
    with col2:
        adresse = st.checkbox('adresse')
    with col3:
        details = st.checkbox('details')
    with col4:
         liens = st.checkbox('liens')
    with col5:
        keywords = st.checkbox('keywords')
    with space:
        pass
    toggle_list = [adresse,details,liens,keywords]
    filt_list = list(compress(['adresse','details','liens','keywords'], toggle_list))
    unis_filt.drop(['keywords_raw']+filt_list,axis=1,inplace=True)
    if toggle_list[2] == False:
        unis_filt['liens'] = unis_filt['liens'].apply(make_clickable)
    unis_filt = unis_filt.to_html(escape=False)
    st.write(unis_filt, unsafe_allow_html=True)

def user():
    st.write("""# User customization""")
    options = st.multiselect('Choisi tes sujets:',list(keyword_dict.keys()))
    kws = options
    itera = 0
    unis_overall = []

    if len(kws) > 0:
        col1, col2, col3, col4, space = st.columns([0.6,1,1,1,16-4])
        with col1:
            st.write("""Hide:""")
        with col2:
            adresse = st.checkbox('adresse')
        with col3:
            details = st.checkbox('details')
        with col4:
             liens = st.checkbox('liens')
        with space:
            pass
        toggle_list = [adresse,details,liens]
        filt_list = list(compress(['adresse','details','liens'], toggle_list))
        for elem in kws:
            line = 0
            unis_perso = unis.copy()
            for i in unis_perso['keywords']:
                for word in i:
                    if word == kws[itera]:
                        break
                else:
                    unis_perso.drop(line,axis=0,inplace=True)

                line += 1
            itera+=1
            unis_overall.append(unis_perso)
        unis_vect_chose = pd.concat(unis_overall)
        unis_vect_chose.drop_duplicates(subset='nom',inplace=True)

        points = np.zeros(len(unis_vect_chose))
        freq_values = []

        for elem in kws:
            count = 0
            temp_values = []
            for i in unis_vect_chose['keywords']:
                if elem in i:
                    points[count] += 1
                    temp_values.append(elem)
                else:
                    temp_values.append('')
                count +=1
            freq_values.append(temp_values)

        unis_vect_chose.insert(3,'frequence',points)
        show_only = st.checkbox('Show only universities with all selected courses')
        if show_only == True:
            unis_vect_chose = unis_vect_chose[unis_vect_chose['frequence'] == len(kws)]
        else:
            unis_vect_chose.drop('frequence',inplace=True,axis=1)
            unis_vect_chose.insert(3,'frequence',points)
            temp_freq_values = pd.DataFrame(freq_values).transpose().dropna().values.tolist()
            temp_freq_values = [' '.join(i).split() for i in temp_freq_values]
            unis_vect_chose.insert(4,'selection',temp_freq_values[:len(unis_vect_chose['frequence'])])
        for i in unis_vect_chose['frequence']:
            if i == len(kws):
                break
        else:
            st.write("*No matches for these subjects*")
        unis_vect_chose.sort_values(by='frequence', ascending=False,inplace=True)
        unis_vect_chose.drop(['keywords','keywords_raw']+filt_list,axis=1,inplace=True)
        unis_vect_chose_xlsx = to_excel(unis_vect_chose.drop('frequence',axis=1))
        st.download_button(label='Download Current table of data',data=unis_vect_chose_xlsx ,file_name= f'unversites_user{kws}.xlsx')
        if toggle_list[2] == False:
            unis_vect_chose['liens'] = unis_vect_chose['liens'].apply(make_clickable)
        unis_vect_chose['frequence'] = unis_vect_chose['frequence'].apply(lambda x: str(int(x))+'/'+str(len(kws)))
        unis_vect_chose.set_index(np.arange(1,len(unis_vect_chose)+1),inplace=True)
        unis_vect_chose_html = unis_vect_chose.to_html(escape=False)
        st.write(unis_vect_chose_html, unsafe_allow_html=True)


def similar():
    st.write("""# Similar Universities""")

    langdata = splm.load_data('fr')
    stop_words = set(stopwords.words('french'))

    unvect = []

    for i in unis['details']:
        word_tokens = word_tokenize(i)
        filtered_sentence = []
        for w in word_tokens:
            if w not in stop_words and len(w)>1:
                filtered_sentence.append(splm.lemmatize(w, langdata))

        sent = ' '.join(filtered_sentence)
        unvect.append(sent)

    unis['unvectored'] = unvect
    unis['unvectored'].mask(unis['unvectored'] == '',inplace=True)
    unis_vect= unis.dropna().reset_index().drop('index',axis=1).copy()


    def similarity(x,y):
        vectorizer = TfidfVectorizer()
        data = vectorizer.fit_transform([unis_vect['unvectored'][x],unis_vect['unvectored'][y]])
        features = vectorizer.get_feature_names()
        dense = data.todense()
        denselist = dense.tolist()
        return cosine_similarity([denselist[0]],[denselist[1]])[0][0]

    similarity_df = []

    for i in range(len(unis_vect)):
        similarity_data = []
        for j in range(len(unis_vect)):
            similarity_data.append(similarity(i,j))
        similarity_df.append(similarity_data)

    similarity_fulldf = pd.DataFrame(similarity_df).transpose()

    val = pd.Series(unis_vect.index,unis_vect['nom']).to_dict()
    choose = st.selectbox('Choose University',val)
    i = val[choose]
    unis_vect_chose = unis_vect.loc[similarity_fulldf[i][(similarity_fulldf[i]>0) & (similarity_fulldf[i]<1)].sort_values(ascending=False).head(5).index]

    col1, col2, col3, col4, space = st.columns([0.6,1,1,1,16-4])
    with col1:
        st.write("""Hide:""")
    with col2:
        adresse = st.checkbox('adresse')
    with col3:
        details = st.checkbox('details')
    with col4:
         liens = st.checkbox('liens')
    with space:
        pass
    toggle_list = [adresse,details,liens]
    filt_list = list(compress(['adresse','details','liens'], toggle_list))

    unis_vect_chose.drop(['keywords','keywords_raw','unvectored']+filt_list,axis=1,inplace=True)
    if toggle_list[2] == False:
        unis_vect_chose['liens'] = unis_vect_chose['liens'].apply(make_clickable)
    unis_vect_chose.set_index(np.arange(1,len(unis_vect_chose)+1),inplace=True)
    unis_vect_chose_html = unis_vect_chose.to_html(escape=False)
    st.write(f'5 similar universities to {choose}')
    st.write(unis_vect_chose_html, unsafe_allow_html=True)


with st.sidebar:
    selected = option_menu(
        menu_title='Orientation SN',
        options=["User", 'Similar Universities', 'Info'],
        icons=['house', 'cloud-upload','water'],
        menu_icon='wifi',
        default_index=0
        )



if selected == "User":
    user()
if selected == "Similar Universities":
    similar()
if selected == "Info":
    main()



