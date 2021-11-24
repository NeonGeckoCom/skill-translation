# <img src='https://0000.us/klatchat/app/files/neon_images/icons/neon_skill.png' card_color="#FF8600" width="50" style="vertical-align:bottom">Translation

## Summary

Translates phrases between languages. Also handles switching TTS/STT languages under Neon Core.

## Requirements

No special required packages for this skill.

## Description

Use this skill to switch between languages for your TTS or STT preferences and to get individual words or sentences translations. Note you can have two STT languages active at the same time. They are called `primary` and `secondary` languages. For example, you can have Neon reply to you in both English and Russian at the same time. The order will be determined by which language is set to primary.

TTS (Neon Speech) options are:

    Danish  
    Dutch  
    English, Australian  
    English, British  
    English, Indian  
    English, US  
    English, Welsh  
    French  
    French, Canadian  
    German  
    Italian  
    Japanese  
    Korean  
    Polish  
    Portuguese, Brazilian  
    Portuguese, European  
    Russian  
    Spanish, European  
    Spanish, Mexican  
    Spanish, US  
    Swedish  
    Turkish  
    Chinese

  
  
STT (User Speech) options are:

    Arabic  
    Chinese (Simplified)  
    Chinese (Traditional)  
    Czech  
    Danish  
    Dutch  
    English  
    Finnish  
    French  
    German  
    Hebrew  
    Indonesian  
    Italian  
    Japanese  
    Korean  
    Polish  
    Portuguese  
    Russian  
    Spanish  
    Swedish  
    Turkish



## Examples

Say:
- speak to me in * (and *)

in order to change your language settings. If your desired option has more than one
dialect, Neon will draw a small table with options for you to choose from. Alternatively, you can say your preferred
answer by saying:
- I prefer ...

You may also say:
- my language is *

to have Neon start speaking and listening in the requested language.

Say:
- translate * to *
 
in order to get your desired single-word or phrase translations.

You can also ask to hear back your current settings by saying:
- what are my language settings

## Location

    ${skills}/translation.neon

## Files

    ${skills}/translation.neon/__init__.py  
    ${skills}/translation.neon/language_from_polly.txt  
    ${skills}/translation.neon/test  
    ${skills}/translation.neon/test/intent  
    ${skills}/translation.neon/test/intent/005.ShowLanguageMenu.intent.json  
    ${skills}/translation.neon/test/intent/006.I_prefer.intent.json  
    ${skills}/translation.neon/test/intent/004.playnow_intent.intent.json  
    ${skills}/translation.neon/test/intent/003.not_now_intent.intent.json  
    ${skills}/translation.neon/test/intent/001.TalkToMeKeyword_intent.intent.json  
    ${skills}/translation.neon/test/intent/002.TalkToYouKeyword_intent.intent.json  
    ${skills}/translation.neon/language_from_stt.txt  
    ${skills}/translation.neon/settings.json  
    ${skills}/translation.neon/vocab  
    ${skills}/translation.neon/vocab/en-us  
    ${skills}/translation.neon/vocab/en-us/gender.voc  
    ${skills}/translation.neon/vocab/en-us/AgreementKeyword.voc  
    ${skills}/translation.neon/vocab/en-us/DeclineKeyword.voc  
    ${skills}/translation.neon/vocab/en-us/I_prefer.voc  
    ${skills}/translation.neon/vocab/en-us/ShowLanguageMenu.voc  
    ${skills}/translation.neon/vocab/en-us/stt_language.voc  
    ${skills}/translation.neon/vocab/en-us/TalkToMeKeyword.voc  
    ${skills}/translation.neon/vocab/en-us/Settings.voc  
    ${skills}/translation.neon/vocab/en-us/Neon.voc  
    ${skills}/translation.neon/vocab/en-us/OnlyOne.voc  
    ${skills}/translation.neon/vocab/en-us/language.voc  
    ${skills}/translation.neon/vocab/en-us/TalkToYouKeyword.voc  
    ${skills}/translation.neon/vocab/en-us/Two.voc  
    ${skills}/translation.neon/README.md

  

## Class Diagram

[Click Here](https://0000.us/klatchat/app/files/neon_images/class_diagrams/translation.png)

## Available Intents
<details>
<summary>Show list</summary>
<br>
### gender.voc  
    male  
    female  
      
### AgreementKeyword.voc  
    yes  
    sure  
    proceed  
    continue  
    begin  
    start  
    go ahead  
    lets do it  
    do it  
    of course  
    actually do  
    changed my mind  
      
### DeclineKeyword.voc  
    no  
    dont  
    not  
    do not  
    stop  
    break  
    leave  
    quit  
    end  
    not now  
    that's enough  
    enough  
    
### I_prefer.voc  
    i prefer  
    i choose  
    
### ShowLanguageMenu.voc  
    show me language menu  
    language menu  
      
### stt_language.voc  
    af-za  
    am-et  
    hy-am  
    az-az  
    id-id  
    ms-my  
    bn-bd  
    ca-es  
    cs-cz  
    da-dk  
    de-de  
    en-gb  
    en-us  
    es-es  
    es-us  
    es-mx  
    eu-es  
    fil-ph  
    fr-ca  
    fr-fr  
    gl-es  
    ka-ge  
    gu-in  
    hr-hr  
    zu-za  
    is-is  
    it-it  
    jv-id  
    kn-in  
    km-kh  
    lo-la  
    lv-lv  
    lt-lt  
    hu-hu  
    ml-in  
    mr-in  
    nl-nl  
    ne-np  
    nb-no  
    pl-pl  
    pt-br  
    pt-pt  
    ro-ro  
    si-lk  
    sk-sk  
    sl-si  
    su-id  
    sw-tz  
    fi-fi  
    sv-se  
    ta-in  
    te-in  
    vi-vn  
    tr-tr  
    ur-pk  
    el-gr  
    bg-bg  
    ru-ru  
    sr-rs  
    uk-ua  
    he-il  
    ar-il  
    fa-ir  
    hi-in  
    th-th  
    ko-kr  
    zh-tw  
    yue-hant-hk  
    ja-jp  
    zh  
      
### TalkToMeKeyword.voc  
    talk to me in  
    speak to me in  
    speak in  
    translate  
    tts in  
    
### Settings.voc  
    tell me my language settings  
    what is my language  
    what is my input language  
    what are my input languages  
    what are my language settings  
    
### Neon.voc  
    neon  
    leon  
    nyan  
    
### OnlyOne.voc  
    only speak to me in one language  
    no secondary language  
    speak only in my primary language  
    only use primary for language  
    use only primary language  
    only use my primary language  
    
### language.voc  
    chinese mandarin  
    danish  
    dutch  
    english australian  
    english british  
    english indian  
    english us  
    english welsh  
    french  
    french canadian  
    hindi  
    german  
    icelandic  
    italian  
    japanese  
    korean  
    norwegian  
    polish  
    portuguese brazilian  
    portuguese european  
    romanian  
    russian  
    spanish european  
    spanish mexican  
    spanish us  
    swedish  
    turkish  
    welsh  
    english  
    portuguese  
    spanish  
    chinese  
      
### TalkToYouKeyword.voc  
    i will (talk|speak) to you  
    i want to (talk|speak) in  
    i am speaking in  
    my language is  
    my preferred language is  
    start listening for  
    starts listening for  
    stt in  
    
### Two.voc  
    two  
    both

</details>  

## Details

### Text

        speak to me in spanish
        >> I am switching to spanish. But I do have other dialect options for you. Say language menu if you would like to hear them
        
        language menu
        >> Sure. Your other options are:
        >> ...
        
        I prefer US spanish
        >> Sounds good
        
        
        Translate hello to Japanese.
        >> hello in Japanese is *Spoken Translation*


### Picture

### Video

  

## Contact Support

Use the [link](https://neongecko.com/ContactUs) or [submit an issue on GitHub](https://help.github.com/en/articles/creating-an-issue)

## Credits
[NeonDaniel](https://github.com/NeonDaniel)
[NeonGeckoCom](https://github.com/NeonGeckoCom)
[reginaneon](https://github.com/reginaneon)
