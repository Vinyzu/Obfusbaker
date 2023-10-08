import ast
import builtins
import random
import string
import textwrap
import re

import python_minifier
import pyperclip

builtins_list = list(dir(builtins))
maximize_protection = False  # Not Recommended without good reasoning. Slows down by 10x or so
indent_masking = True  # Recommended. Fucks up Editors and only about 1.2x slowdown
min_indent_space = 1000

old_unicode_chars = "𝠀𝠁𝠂𝠃𝠄𝠅𝠆𝠇𝠈𝠉𝠊𝠋𝠌𝠍𝠎𝠏𝠐𝠑𝠒𝠓𝠔𝠕𝠖𝠗𝠘𝠙𝠚𝠛𝠜𝠝𝠞𝠟𝠠𝠡𝠢𝠣𝠤𝠥𝠦𝠧𝠨𝠩𝠪𝠫𝠬𝠭𝠮𝠯𝠰𝠱𝠲𝠳𝠴𝠵𝠶𝠷𝠸𝠹𝠺𝠻𝠼𝠽𝠾𝠿𝡀𝡁𝡂𝡃𝡄𝡅𝡆𝡇𝡈𝡉𝡊𝡋𝡌𝡍𝪛𝡎𝡏𝡐𝡑𝡒𝡓𝡔𝡕𝡖𝡗𝡘𝡙𝡚𝡛𝡜𝡝𝡞𝡟𝡠𝡡𝡢𝡣𝡤𝡥𝡦𝡧𝡨𝡩𝡪𝡫𝡬𝡭𝡮𝡯𝡰𝡱𝡲𝡳𝡴𝡵𝡶𝡷𝡸𝡹𝡺𝡻𝡼𝡽𝡾𝡿𝢀𝢁𝢂𝢃𝢄𝢅𝢆𝢇𝢈𝢉𝢊𝢋𝢌𝢍𝢎𝢏𝢐𝢑𝢒𝢓𝢔𝢕𝢖𝢗𝢘𝢙𝢚𝢛𝢜𝢝𝢞𝢟𝢠𝢡𝢢𝢣𝢤𝢥𝢦𝢧𝢨𝢩𝢪𝢫𝢬𝢭𝢮𝢯𝢰𝢱𝢲𝢳𝢴𝢵𝢶𝢷𝢸𝢹𝢺𝢻𝢼𝢽𝢾𝢿𝣀𝣁𝣂𝣃𝣄𝣅𝣆𝣇𝣈𝣉𝣊𝣋𝣌𝣍𝣎𝣏𝣐𝣑𝣒𝣓𝣔𝣕𝣖𝣗𝣘𝣙𝣚𝣛𝣜𝣝𝣞𝣟𝣠𝣡𝣢𝣣𝣤𝣥𝣦𝣧𝣨𝣩𝣪𝣫𝣬𝣭𝣮𝣯𝣰𝣱𝣲𝣳𝣴𝣵𝣶𝣷𝣸𝣹𝣺𝣻𝣼𝣽𝣾𝣿𝤀𝤁𝤂𝤃𝤄𝤅𝤆𝤇𝤈𝤉𝤊𝤋𝤌𝤍𝤎𝤏𝤐𝤑𝤒𝤓𝤔𝤕𝤖𝤗𝤘𝤙𝤚𝤛𝤜𝤝𝤞𝤟𝤠𝤡𝤢𝤣𝤤𝤥𝤦𝤧𝤨𝤩𝤪𝤫𝤬𝤭𝤮𝤯𝤰𝤱𝤲𝤳𝤴𝤵𝤶𝤷𝤸𝤹𝤺𝤻𝤼𝤽𝤾𝤿𝥀𝥁𝥂𝥃𝥄𝥅𝥆𝥇𝥈𝥉𝥊𝥋𝥌𝥍𝥎𝥏𝥐𝥑𝥒𝥓𝥔𝥕𝥖𝥗𝥘𝥙𝥚𝥛𝥜𝥝𝥞𝥟𝥠𝥡𝥢𝥣𝥤𝥥𝥦𝥧𝥨𝥩𝥪𝥫𝥬𝥭𝥮𝥯𝥰𝥱𝥲𝥳𝥴𝥵𝥶𝥷𝥸𝥹𝥺𝥻𝥼𝥽𝥾𝥿𝦀𝦁𝦂𝦃𝦄𝦅𝦆𝦇𝦈𝦉𝦊𝦋𝦌𝦍𝦎𝦏𝦐𝦑𝦒𝦓𝦔𝦕𝦖𝦗𝦘𝦙𝦚𝦛𝦜𝦝𝦞𝦟𝦠𝦡𝦢𝦣𝦤𝦥𝦦𝦧𝦨𝦩𝦪𝦫𝦬𝦭𝦮𝦯𝦰𝦱𝦲𝦳𝦴𝦵𝦶𝦷𝦸𝦹𝦺𝦻𝦼𝦽𝦾𝦿𝧀𝧁𝧂𝧃𝧄𝧅𝧆𝧇𝧈𝧉𝧊𝧋𝧌𝧍𝧎𝧏𝧐𝧑𝧒𝧓𝧔𝧕𝧖𝧗𝧘𝧙𝧚𝧛𝧜𝧝𝧞𝧟𝧠𝧡𝧢𝧣𝧤𝧥𝧦𝧧𝧨𝧩𝧪𝧫𝧬𝧭𝧮𝧯𝧰𝧱𝧲𝧳𝧴𝧵𝧶𝧷𝧸𝧹𝧺𝧻𝧼𝧽𝧾𝧿𝨀𝨁𝨂𝨃𝨄𝨅𝨆𝨇𝨈𝨉𝨊𝨋𝨌𝨍𝨎𝨏𝨐𝨑𝨒𝨓𝨔𝨕𝨖𝨗𝨘𝨙𝨚𝨛𝨜𝨝𝨞𝨟𝨠𝨡𝨢𝨣𝨤𝨥𝨦𝨧𝨨𝨩𝨪𝨫𝨬𝨭𝨮𝨯𝨰𝨱𝨲𝨳𝨴𝨵𝨶𝨷𝨸𝨹𝨺𝨻𝨼𝨽𝨾𝨿𝩀𝩁𝩂𝩃𝩄𝩅𝩆𝩇𝩈𝩉𝩊𝩋𝩌𝩍𝩎𝩏𝩐𝩑𝩒𝩓𝩔𝩕𝩖𝩗𝩘𝩙𝩚𝩛𝩜𝩝𝩞𝩟𝩠𝩡𝩢𝩣𝩤𝩥𝩦𝩧𝩨𝩩𝩪𝩫𝩬𝩭𝩮𝩯𝩰𝩱𝩲𝩳𝩴𝩵𝩶𝩷𝩸𝩹𝩺𝩻𝩼𝩽𝩾𝩿𝪀𝪁𝪂𝪃𝪄𝪅𝪆𝪇𝪈𝪉𝪊𝪋"
unicode_chars = "𘠀𘠁𘠂𘠃𘠄𘠅𘠆𘠇𘠈𘠉𘠊𘠋𘠌𘠍𘠎𘠏𘠐𘠑𘠒𘠓𘠔𘠕𘠖𘠗𘠘𘠙𘠚𘠛𘠜𘠝𘠞𘠟𘠠𘠡𘠢𘠣𘠤𘠥𘠦𘠧𘠨𘠩𘠪𘠫𘠬𘠭𘠮𘠯𘠰𘠱𘠲𘠳𘠴𘠵𘠶𘠷𘠸𘠹𘠺𘠻𘠼𘠽𘠾𘠿𘡀𘡁𘡂𘡃𘡄𘡅𘡆𘡇𘡈𘡉𘡊𘡋𘡌𘡍𘡎𘡏𘡐𘡑𘡒𘡓𘡔𘡕𘡖𘡗𘡘𘡙𘡚𘡛𘡜𘡝𘡞𘡟𘡠𘡡𘡢𘡣𘡤𘡥𘡦𘡧𘡨𘡩𘡪𘡫𘡬𘡭𘡮𘡯𘡰𘡱𘡲𘡳𘡴𘡵𘡶𘡷𘡸𘡹𘡺𘡻𘡼𘡽𘡾𘡿𘢀𘢁𘢂𘢃𘢄𘢅𘢆𘢇𘢈𘢉𘢊𘢋𘢌𘢍𘢎𘢏𘢐𘢑𘢒𘢓𘢔𘢕𘢖𘢗𘢘𘢙𘢚𘢛𘢜𘢝𘢞𘢟𘢠𘢡𘢢𘢣𘢤𘢥𘢦𘢧𘢨𘢩𘢪𘢫𘢬𘢭𘢮𘢯𘢰𘢱𘢲𘢳𘢴𘢵𘢶𘢷𘢸𘢹𘢺𘢻𘢼𘢽𘢾𘢿𘣀𘣁𘣂𘣃𘣄𘣅𘣆𘣇𘣈𘣉𘣊𘣋𘣌𘣍𘣎𘣏𘣐𘣑𘣒𘣓𘣔𘣕𘣖𘣗𘣘𘣙𘣚𘣛𘣜𘣝𘣞𘣟𘣠𘣡𘣢𘣣𘣤𘣥𘣦𘣧𘣨𘣩𘣪𘣫𘣬𘣭𘣮𘣯𘣰𘣱𘣲𘣳𘣴𘣵𘣶𘣷𘣸𘣹𘣺𘣻𘣼𘣽𘣾𘣿𘤀𘤁𘤂𘤃𘤄𘤅𘤆𘤇𘤈𘤉𘤊𘤋𘤌𘤍𘤎𘤏𘤐𘤑𘤒𘤓𘤔𘤕𘤖𘤗𘤘𘤙𘤚𘤛𘤜𘤝𘤞𘤟𘤠𘤡𘤢𘤣𘤤𘤥𘤦𘤧𘤨𘤩𘤪𘤫𘤬𘤭𘤮𘤯𘤰𘤱𘤲𘤳𘤴𘤵𘤶𘤷𘤸𘤹𘤺𘤻𘤼𘤽𘤾𘤿𘥀𘥁𘥂𘥃𘥄𘥅𘥆𘥇𘥈𘥉𘥊𘥋𘥌𘥍𘥎𘥏𘥐𘥑𘥒𘥓𘥔𘥕𘥖𘥗𘥘𘥙𘥚𘥛𘥜𘥝𘥞𘥟𘥠𘥡𘥢𘥣𘥤𘥥𘥦𘥧𘥨𘥩𘥪𘥫𘥬𘥭𘥮𘥯𘥰𘥱𘥲𘥳𘥴𘥵𘥶𘥷𘥸𘥹𘥺𘥻𘥼𘥽𘥾𘥿𘦀𘦁𘦂𘦃𘦄𘦅𘦆𘦇𘦈𘦉𘦊𘦋𘦌𘦍𘦎𘦏𘦐𘦑𘦒𘦓𘦔𘦕𘦖𘦗𘦘𘦙𘦚𘦛𘦜𘦝𘦞𘦟𘦠𘦡𘦢𘦣𘦤𘦥𘦦𘦧𘦨𘦩𘦪𘦫𘦬𘦭𘦮𘦯𘦰𘦱𘦲𘦳𘦴𘦵𘦶𘦷𘦸𘦹𘦺𘦻𘦼𘦽𘦾𘦿𘧀𘧁𘧂𘧃𘧄𘧅𘧆𘧇𘧈𘧉𘧊𘧋𘧌𘧍𘧎𘧏𘧐𘧑𘧒𘧓𘧔𘧕𘧖𘧗𘧘𘧙𘧚𘧛𘧜𘧝𘧞𘧟𘧠𘧡𘧢𘧣𘧤𘧥𘧦𘧧𘧨𘧩𘧪𘧫𘧬𘧭𘧮𘧯𘧰𘧱𘧲𘧳𘧴𘧵𘧶𘧷𘧸𘧹𘧺𘧻𘧼𘧽𘧾𘧿𘨀𘨁𘨂𘨃𘨄𘨅𘨆𘨇𘨈𘨉𘨊𘨋𘨌𘨍𘨎𘨏𘨐𘨑𘨒𘨓𘨔𘨕𘨖𘨗𘨘𘨙𘨚𘨛𘨜𘨝𘨞𘨟𘨠𘨡𘨢𘨣𘨤𘨥𘨦𘨧𘨨𘨩𘨪𘨫𘨬𘨭𘨮𘨯𘨰𘨱𘨲𘨳𘨴𘨵𘨶𘨷𘨸𘨹𘨺𘨻𘨼𘨽𘨾𘨿𘩀𘩁𘩂𘩃𘩄𘩅𘩆𘩇𘩈𘩉𘩊𘩋𘩌𘩍𘩎𘩏𘩐𘩑𘩒𘩓𘩔𘩕𘩖𘩗𘩘𘩙𘩚𘩛𘩜𘩝𘩞𘩟𘩠𘩡𘩢𘩣𘩤𘩥𘩦𘩧𘩨𘩩𘩪𘩫𘩬𘩭𘩮𘩯𘩰𘩱𘩲𘩳𘩴𘩵𘩶𘩷𘩸𘩹𘩺𘩻𘩼𘩽𘩾𘩿𘪀𘪁𘪂𘪃𘪄𘪅𘪆𘪇𘪈𘪉𘪊𘪋𘪌𘪍𘪎𘪏𘪐𘪑𘪒𘪓𘪔𘪕𘪖𘪗𘪘𘪙𘪚𘪛𘪜𘪝𘪞𘪟𘪠𘪡𘪢𘪣𘪤𘪥𘪦𘪧𘪨𘪩𘪪𘪫𘪬𘪭𘪮𘪯𘪰𘪱𘪲𘪳𘪴𘪵𘪶𘪷𘪸𘪹𘪺𘪻𘪼𘪽𘪾𘪿𘫀𘫁𘫂𘫃𘫄𘫅𘫆𘫇𘫈𘫉𘫊𘫋𘫌𘫍𘫎𘫏𘫐𘫑𘫒𘫓𘫔𘫕𘫖𘫗𘫘𘫙𘫚𘫛𘫜𘫝𘫞𘫟𘫠𘫡𘫢𘫣𘫤𘫥𘫦𘫧𘫨𘫩𘫪𘫫𘫬𘫭𘫮𘫯𘫰𘫱𘫲𘫳𘫴𘫵𘫶𘫷𘫸𘫹𘫺𘫻𘫼𘫽𘫾𘫿🨀🨁🨂🨃🨄🨅🨆🨇🨈🨉🨊🨋🨌🨍🨎🨏🨐🨑🨒🨓🨔🨕🨖🨗🨘🨙🨚🨛🨜🨝🨞🨟🨠🨡🨢🨣🨤🨥🨦🨧🨨🨩🨪🨫🨬🨭🨮🨯🨰🨱🨲🨳🨴🨵🨶🨷🨸🨹🨺🨻🨼🨽🨾🨿🩀🩁🩂🩃🩄🩅🩆🩇🩈🩉🩊🩋🩌🩍🩎🩏🩐🩑🩒🩓🩠🩡🩢🩣🩤🩥🩦🩧🩨🩩🩪🩫🩬🩭𜼀𜼁𜼂𜼃𜼄𜼅𜼆𜼇𜼈𜼉𜼊𜼋𜼌𜼍𜼎𜼏𜼐𜼑𜼒𜼓𜼔𜼕𜼖𜼗𜼘𜼙𜼚𜼛𜼜𜼝𜼞𜼟𜼠𜼡𜼢𜼣𜼤𜼥𜼦𜼧𜼨𜼩𜼪𜼫𜼬𜼭𜼰𜼱𜼲𜼳𜼴𜼵𜼶𜼷𜼸𜼹𜼺𜼻𜼼𜼽𜼾𜼿𜽀𜽁𜽂𜽃𜽄𜽅𜽆𜽐𜽑𜽒𜽓𜽔𜽕𜽖𜽗𜽘𜽙𜽚𜽛𜽜𜽝𜽞𜽟𜽠𜽡𜽢𜽣𜽤𜽥𜽦𜽧𜽨𜽩𜽪𜽫𜽬𜽭𜽮𜽯𜽰𜽱𜽲𜽳𜽴𜽵𜽶𜽷𜽸𜽹𜽺𜽻𜽼𜽽𜽾𜽿𜾀𜾁𜾂𜾃𜾄𜾅𜾆𜾇𜾈𜾉𜾊𜾋𜾌𜾍𜾎𜾏𜾐𜾑𜾒𜾓𜾔𜾕𜾖𜾗𜾘𜾙𜾚𜾛𜾜𜾝𜾞𜾟𜾠𜾡𜾢𜾣𜾤𜾥𜾦𜾧𜾨𜾩𜾪𜾫𜾬𜾭𜾮𜾯𜾰𜾱𜾲𜾳𜾴𜾵𜾶𜾷𜾸𜾹𜾺𜾻𜾼𜾽𜾾𜾿𜿀𜿁𜿂𜿃𑰀𑰁𑰂𑰃𑰄𑰅𑰆𑰇𑰈𑰊𑰋𑰌𑰍𑰎𑰏𑰐𑰑𑰒𑰓𑰔𑰕𑰖𑰗𑰘𑰙𑰚𑰛𑰜𑰝𑰞𑰟𑰠𑰡𑰢𑰣𑰤𑰥𑰦𑰧𑰨𑰩𑰪𑰫𑰬𑰭𑰮𑰯𑰰𑰱𑰲𑰳𑰴𑰵𑰶𑰸𑰹𑰺𑰻𑰼𑰽𑰾𑰿𑱀𑱁𑱂𑱃𑱄𑱅𑱐𑱑𑱒𑱓𑱔𑱕𑱖𑱗𑱘𑱙𑱚𑱛𑱜𑱝𑱞𑱟𑱠𑱡𑱢𑱣𑱤𑱥𑱦𑱧𑱨𑱩𑱪𑱫𑱬𞴁𞴂𞴃𞴄𞴅𞴆𞴇𞴈𞴉𞴊𞴋𞴌𞴍𞴎𞴏𞴐𞴑𞴒𞴓𞴔𞴕𞴖𞴗𞴘𞴙𞴚𞴛𞴜𞴝𞴞𞴟𞴠𞴡𞴢𞴣𞴤𞴥𞴦𞴧𞴨𞴩𞴪𞴫𞴬𞴭𞴮𞴯𞴰𞴱𞴲𞴳𞴴𞴵𞴶𞴷𞴸𞴹𞴺𞴻𞴼𞴽𑵠𑵡𑵢𑵣𑵤𑵥𑵧𑵨𑵪𑵫𑵬𑵭𑵮𑵯𑵰𑵱𑵲𑵳𑵴𑵵𑵶𑵷𑵸𑵹𑵺𑵻𑵼𑵽𑵾𑵿𑶀𑶁𑶂𑶃𑶄𑶅𑶆𑶇𑶈𑶉𑶊𑶋𑶌𑶍𑶎𑶐𑶑𑶓𑶔𑶕𑶖𑶠𑶡𑶢𑶣𑶤𑶥𑶦𑶧𑶨𑶩𞓐𞓑𞓒𞓓𞓔𞓕𞓖𞓗𞓘𞓙𞓚𞓛𞓜𞓝𞓞𞓟𞓠𞓡𞓢𞓣𞓤𞓥𞓦𞓧𞓨𞓩𞓪𞓫𞓮𞓯𞓬𞓭𞓰𞓱𞓲𞓳𞓴𞓵𞓶𞓷𞓸𞓹𖩰𖩱𖩲𖩳𖩴𖩵𖩶𖩷𖩸𖩹𖩺𖩻𖩼𖩽𖩾𖩿𖪀𖪁𖪂𖪃𖪄𖪅𖪆𖪇𖪈𖪉𖪊𖪋𖪌𖪍𖪎𖪏𖪐𖪑𖪒𖪓𖪔𖪕𖪖𖪗𖪘𖪙𖪚𖪛𖪜𖪝𖪞𖪟𖪠𖪡𖪢𖪣𖪤𖪥𖪦𖪧𖪨𖪩𖪪𖪫𖪬𖪭𖪮𖪯𖪰𖪱𖪲𖪳𖪴𖪵𖪶𖪷𖪸𖪹𖪺𖪻𖪼𖪽𖪾𖫀𖫁𖫂𖫃𖫄𖫅𖫆𖫇𖫈𖫉ᨠᨡᨢᨣᨤᨥᨦᨧᨨᨩᨪᨫᨬᨭᨮᨯᨰᨱᨲᨳᨴᨵᨶᨷᨸᨹᨺᨻᨼᨽᨾᨿᩀᩁᩂᩃᩄᩅᩆᩇᩈᩉᩊᩋᩌᩍᩎᩏᩐᩑᩒᩓᩔᩕ ᩖᩗᩘᩙᩚᩛᩜᩝᩞ᩠ᩡᩢᩣᩤᩥᩦᩧᩨᩩᩪᩫᩬᩭᩮᩯᩰᩱᩲᩳᩴ᩿᩵᩶᩷᩸᩹᩺᩻᩼᪀᪁᪂᪃᪄᪅᪆᪇᪈᪉᪐᪑᪒᪓᪔᪕᪖᪗᪘᪙᪠᪡᪢᪣᪤᪥᪦ᪧ᪨᪩᪪᪫᪬᪭𑐀𑐁𑐂𑐃𑐄𑐅𑐆𑐇𑐈𑐉𑐊𑐋𑐌𑐍𑐎𑐏𑐐𑐑𑐒𑐓𑐔𑐕𑐖𑐗𑐘𑐙𑐚𑐛𑐜𑐝𑐞𑐟𑐠𑐡𑐢𑐣𑐤𑐥𑐦𑐧𑐨𑐩𑐪𑐫𑐬𑐭𑐮𑐯𑐰𑐱𑐲𑐳𑐴𑐵𑐶𑐷𑐸𑐹𑐺𑐻𑐼𑐽𑐾𑐿𑑀𑑁𑑂𑑃𑑄𑑅𑑆𑑇𑑈𑑉𑑊𑑋𑑌𑑍𑑎𑑏𑑐𑑑𑑒𑑓𑑔𑑕𑑖𑑗𑑘𑑙𑑚𑑛𑑝𑑞𑑟𑖀𑖁𑖂𑖃𑖄𑖅𑖆𑖇𑖈𑖉𑖊𑖋𑖌𑖍𑖎𑖏𑖐𑖑𑖒𑖓𑖔𑖕𑖖𑖗𑖘𑖙𑖚𑖛𑖜𑖝𑖞𑖟𑖠𑖡𑖢𑖣𑖤𑖥𑖦𑖧𑖨𑖩𑖪𑖫𑖬𑖭𑖮𑖯𑖰𑖱𑖲𑖳𑖴𑖵𑖸𑖹𑖺𑖻𑖼𑖽𑖾𑗀𑖿𑗁𑗂𑗃𑗄𑗅𑗆𑗇𑗈𑗉𑗊𑗋𑗌𑗍𑗎𑗏𑗐𑗑𑗒𑗓𑗔𑗕𑗖𑗗𑗘𑗙𑗚𑗛𑗜𑗝𑱰𑱱𑱲𑱳𑱴𑱵𑱶𑱷𑱸𑱹𑱺𑱻𑱼𑱽𑱾𑱿𑲀𑲁𑲂𑲃𑲄𑲅𑲆𑲇𑲈𑲉𑲊𑲋𑲌𑲍𑲎𑲏𑲒𑲓𑲔𑲕𑲖𑲗𑲘𑲙𑲚𑲛𑲜𑲝𑲞𑲟𑲠𑲡𑲢𑲣𑲤𑲥𑲦𑲧𑲩𑲪𑲫𑲬𑲭𑲮𑲯𑲰𑲱𑲲𑲳𑲴𑲵𑲶𑻠𑻡𑻢𑻣𑻤𑻥𑻦𑻧𑻨𑻩𑻪𑻫𑻬𑻭𑻮𑻯𑻰𑻱𑻲𑻳𑻴𑻵𑻶𑻷𑻸𝠀𝠁𝠂𝠃𝠄𝠅𝠆𝠇𝠈𝠉𝠊𝠋𝠌𝠍𝠎𝠏𝠐𝠑𝠒𝠓𝠔𝠕𝠖𝠗𝠘𝠙𝠚𝠛𝠜𝠝𝠞𝠟𝠠𝠡𝠢𝠣𝠤𝠥𝠦𝠧𝠨𝠩𝠪𝠫𝠬𝠭𝠮𝠯𝠰𝠱𝠲𝠳𝠴𝠵𝠶𝠷𝠸𝠹𝠺𝠻𝠼𝠽𝠾𝠿𝡀𝡁𝡂𝡃𝡄𝡅𝡆𝡇𝡈𝡉𝡊𝡋𝡌𝡍𝪛𝡎𝡏𝡐𝡑𝡒𝡓𝡔𝡕𝡖𝡗𝡘𝡙𝡚𝡛𝡜𝡝𝡞𝡟𝡠𝡡𝡢𝡣𝡤𝡥𝡦𝡧𝡨𝡩𝡪𝡫𝡬𝡭𝡮𝡯𝡰𝡱𝡲𝡳𝡴𝡵𝡶𝡷𝡸𝡹𝡺𝡻𝡼𝡽𝡾𝡿𝢀𝢁𝢂𝢃𝢄𝢅𝢆𝢇𝢈𝢉𝢊𝢋𝢌𝢍𝢎𝢏𝢐𝢑𝢒𝢓𝢔𝢕𝢖𝢗𝢘𝢙𝢚𝢛𝢜𝢝𝢞𝢟𝢠𝢡𝢢𝢣𝢤𝢥𝢦𝢧𝢨𝢩𝢪𝢫𝢬𝢭𝢮𝢯𝢰𝢱𝢲𝢳𝢴𝢵𝢶𝢷𝢸𝢹𝢺𝢻𝢼𝢽𝢾𝢿𝣀𝣁𝣂𝣃𝣄𝣅𝣆𝣇𝣈𝣉𝣊𝣋𝣌𝣍𝣎𝣏𝣐𝣑𝣒𝣓𝣔𝣕𝣖𝣗𝣘𝣙𝣚𝣛𝣜𝣝𝣞𝣟𝣠𝣡𝣢𝣣𝣤𝣥𝣦𝣧𝣨𝣩𝣪𝣫𝣬𝣭𝣮𝣯𝣰𝣱𝣲𝣳𝣴𝣵𝣶𝣷𝣸𝣹𝣺𝣻𝣼𝣽𝣾𝣿𝤀𝤁𝤂𝤃𝤄𝤅𝤆𝤇𝤈𝤉𝤊𝤋𝤌𝤍𝤎𝤏𝤐𝤑𝤒𝤓𝤔𝤕𝤖𝤗𝤘𝤙𝤚𝤛𝤜𝤝𝤞𝤟𝤠𝤡𝤢𝤣𝤤𝤥𝤦𝤧𝤨𝤩𝤪𝤫𝤬𝤭𝤮𝤯𝤰𝤱𝤲𝤳𝤴𝤵𝤶𝤷𝤸𝤹𝤺𝤻𝤼𝤽𝤾𝤿𝥀𝥁𝥂𝥃𝥄𝥅𝥆𝥇𝥈𝥉𝥊𝥋𝥌𝥍𝥎𝥏𝥐𝥑𝥒𝥓𝥔𝥕𝥖𝥗𝥘𝥙𝥚𝥛𝥜𝥝𝥞𝥟𝥠𝥡𝥢𝥣𝥤𝥥𝥦𝥧𝥨𝥩𝥪𝥫𝥬𝥭𝥮𝥯𝥰𝥱𝥲𝥳𝥴𝥵𝥶𝥷𝥸𝥹𝥺𝥻𝥼𝥽𝥾𝥿𝦀𝦁𝦂𝦃𝦄𝦅𝦆𝦇𝦈𝦉𝦊𝦋𝦌𝦍𝦎𝦏𝦐𝦑𝦒𝦓𝦔𝦕𝦖𝦗𝦘𝦙𝦚𝦛𝦜𝦝𝦞𝦟𝦠𝦡𝦢𝦣𝦤𝦥𝦦𝦧𝦨𝦩𝦪𝦫𝦬𝦭𝦮𝦯𝦰𝦱𝦲𝦳𝦴𝦵𝦶𝦷𝦸𝦹𝦺𝦻𝦼𝦽𝦾𝦿𝧀𝧁𝧂𝧃𝧄𝧅𝧆𝧇𝧈𝧉𝧊𝧋𝧌𝧍𝧎𝧏𝧐𝧑𝧒𝧓𝧔𝧕𝧖𝧗𝧘𝧙𝧚𝧛𝧜𝧝𝧞𝧟𝧠𝧡𝧢𝧣𝧤𝧥𝧦𝧧𝧨𝧩𝧪𝧫𝧬𝧭𝧮𝧯𝧰𝧱𝧲𝧳𝧴𝧵𝧶𝧷𝧸𝧹𝧺𝧻𝧼𝧽𝧾𝧿𝨀𝨁𝨂𝨃𝨄𝨅𝨆𝨇𝨈𝨉𝨊𝨋𝨌𝨍𝨎𝨏𝨐𝨑𝨒𝨓𝨔𝨕𝨖𝨗𝨘𝨙𝨚𝨛𝨜𝨝𝨞𝨟𝨠𝨡𝨢𝨣𝨤𝨥𝨦𝨧𝨨𝨩𝨪𝨫𝨬𝨭𝨮𝨯𝨰𝨱𝨲𝨳𝨴𝨵𝨶𝨷𝨸𝨹𝨺𝨻𝨼𝨽𝨾𝨿𝩀𝩁𝩂𝩃𝩄𝩅𝩆𝩇𝩈𝩉𝩊𝩋𝩌𝩍𝩎𝩏𝩐𝩑𝩒𝩓𝩔𝩕𝩖𝩗𝩘𝩙𝩚𝩛𝩜𝩝𝩞𝩟𝩠𝩡𝩢𝩣𝩤𝩥𝩦𝩧𝩨𝩩𝩪𝩫𝩬𝩭𝩮𝩯𝩰𝩱𝩲𝩳𝩴𝩵𝩶𝩷𝩸𝩹𝩺𝩻𝩼𝩽𝩾𝩿𝪀𝪁𝪂𝪃𝪄𝪅𝪆𝪇𝪈𝪉𝪊𝪋"
modifier = "𑻠"
unicode_dict = {char: chr(i) for i, char in enumerate(unicode_chars)}

class Helpers:
    def decimal_to_base3(decimal_num):
        if decimal_num == 0:
            return 0

        base3_digits = []
        while decimal_num > 0:
            remainder = decimal_num % 3
            base3_digits.append(remainder)
            decimal_num //= 3

        base3_digits.reverse()
        base3_result = int(''.join(map(str, base3_digits)))

        return base3_result

    def encode_string(input_string):
        return ''.join([unicode_chars[ord(char)] if ord(char) <= len(unicode_chars) else modifier+char for char in input_string])


    def encode_float(input_int):
        return Helpers.encode_string(str(input_int))

    def decode_float(encoded_float):
        return f"float(decode_string({encoded_float})')"

class ValueObfuscator(ast.NodeTransformer):
    def __init__(self):
        super().__init__()

    def visit_JoinedStr(self, node):
        new_values = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                encoded = Helpers.encode_string(value.value)
                call = ast.Call(func=ast.Name(id='decode_string', ctx=ast.Load()), args=[ast.Constant(value=encoded)], keywords=[])
                value = ast.FormattedValue(value=call, conversion=-1)
            new_values.append(value)
        node.values = new_values
        return node

    def visit_Str(self, node):
        encoded = Helpers.encode_string(node.s)
        call = ast.Call(func=ast.Name(id='decode_string', ctx=ast.Load()), args=[ast.Constant(value=encoded)], keywords=[])
        return call

    def visit_Num(self, node):
        if isinstance(node.n, int):
            encoded = Helpers.encode_string(str(node.n))
            call1 = ast.Call(func=ast.Name(id='decode_string', ctx=ast.Load()), args=[ast.Constant(value=encoded)], keywords=[])
            call2 = ast.Call(func=ast.Name(id='int', ctx=ast.Load()), args=[call1], keywords=[])
            return call2
        elif isinstance(node.n, float):
            encoded = Helpers.encode_string(str(node.n))
            call1 = ast.Call(func=ast.Name(id='decode_string', ctx=ast.Load()), args=[ast.Constant(value=encoded)], keywords=[])
            call2 = ast.Call(func=ast.Name(id='float', ctx=ast.Load()), args=[call1], keywords=[])
            return call2

    def visit_NameConstant(self, node):
        if isinstance(node.value, bool):
            bool_int = random.randint(1000, 999999) if node.value else 0

            first, second = random.randint(-999999, 999999), random.randint(-999999, 999999)
            third = (bool_int-first-second)

            first, second, third = ast.Constant(value=first), ast.Constant(value=second), ast.Constant(value=third)
            first, second, third = self.visit(first), self.visit(second,), self.visit(third)

            call1 = ast.Call(func=ast.Name(id='sum', ctx=ast.Load()), args=[ast.List(elts=[first, second, third], ctx=ast.Load())], keywords=[])
            call2 = ast.Call(func=ast.Name(id='bool', ctx=ast.Load()), args=[call1], keywords=[])
            return call2
        # elif node.value == None:
        #     letters = ''.join(random.sample(string.ascii_lowercase, 9))
        #     encoded = Helpers.encode_string(f"{letters} = '{letters}'")
        #     decode_call = ast.Call(func=ast.Name(id=self.rename('decode_string'), ctx=ast.Load()), args=[ast.Constant(value=encoded)], keywords=[])
        #     call2 = ast.Call(func=ast.Name(id=self.rename('exec'), ctx=ast.Load()), args=[decode_call], keywords=[])
        #     return call2
        return node


class ConstantObfuscator(ast.NodeTransformer):
    def __init__(self):
        super().__init__()
        self.value_obfuscator = ValueObfuscator()

        self.mapping = {}
        self.imports = {}
        self.count = 0
        self.current_class_name = False
        self.in_function = False

        self.ignores = []
        # Append all python methods to ignores
        for builtin in __builtins__.__dict__.values():
            for method in list(dir(builtin)):
                self.ignores.append(method)

        self.compare_ops = []
        for compare_op in ["==", "!=", "<", "<=", ">", ">=", "is", "is not", "in", "not in"]:
            x, y = self.hashed_random_string(), self.hashed_random_string()
            self.compare_ops.append(f"lambda {x}, {y}: {x} {compare_op} {y}")

        builtins_list.extend(self.compare_ops)

        self.builtins_scramble = {}
        for builtin in builtins_list:
            self.builtins_scramble[builtin] = self.hashed_random_string()

        self.builtins_scramble[f"{unicode_dict}"] = self.rename("unicode_dict")

    def hashed_random_string(self):
        new = "𑻠"
        base3_count = Helpers.decimal_to_base3(self.count)

        for num in str(base3_count):
            if int(num) % 3 == 0:
                new += "𝨗"
            elif int(num) % 2 == 0:
                new += "𝨨"
            else:
                new += "𝨻"

        self.count += 1
        return new

    def rename(self, input, subcall=False):
        input = str(input)

        if input in self.ignores and subcall:
            return

        if input in builtins_list:
            return self.builtins_scramble[input]

        elif input in self.imports:
            return self.imports[input]

        elif input in self.mapping:
            return self.mapping[input]

        new_name = self.hashed_random_string()
        self.mapping[input] = new_name
        return new_name

    # ------------------------------- Imports -------------------------------
    def visit_Import(self, node):
        targets = []
        values = []

        for name in node.names:
            new_name = self.value_obfuscator.visit(ast.Constant(value=name.name))
            new_name = self.visit(new_name)
            import_call = ast.Call(func=ast.Name(id=self.rename('__import__'), ctx=ast.Load()), args=[new_name], keywords=[])

            hashed = self.hashed_random_string()
            targets.append(ast.Name(id=hashed, ctx=ast.Store()))
            self.mapping[name.asname if name.asname else name.name] = hashed
            values.append(import_call)

        if len(targets) == 1:
            new_node = ast.Assign(targets=targets, value=values[0], ctx=ast.Load())
        else:
            new_node = ast.Assign(targets=[ast.Tuple(elts=targets, ctx=ast.Store())], value=ast.Tuple(elts=values), ctx=ast.Load())

        new_node.lineno = node.lineno
        return new_node

    def visit_ImportFrom(self, node):
        name = self.value_obfuscator.visit(ast.Constant(value=node.module))
        name = self.visit(name)
        main_import_call = ast.Call(func=ast.Name(id=self.rename('__import__'), ctx=ast.Load()), args=[name], keywords=[])

        targets = []
        values = []

        for name in node.names:
            new_name = self.value_obfuscator.visit(ast.Constant(value=name.name))
            new_name = self.visit(new_name)
            import_call = ast.Call(func=ast.Name(id=self.rename('getattr'), ctx=ast.Load()), args=[main_import_call, new_name], keywords=[])

            hashed = self.hashed_random_string()
            targets.append(ast.Name(id=hashed, ctx=ast.Store()))
            self.mapping[name.asname if name.asname else name.name] = hashed
            values.append(import_call)

        if len(targets) == 1:
            new_node = ast.Assign(targets=targets, value=values[0], ctx=ast.Load())
        else:
            new_node = ast.Assign(targets=[ast.Tuple(elts=targets, ctx=ast.Store())], value=ast.Tuple(elts=values), ctx=ast.Load())

        new_node.lineno = node.lineno
        return new_node

    # ------------------------------- Definitions -------------------------------
    def visit_FunctionDef(self, node):
        if not (node.name.startswith('__') and node.name.endswith("__")) and not self.current_class_name:
            if new_name := self.rename(node.name):
                node.name = new_name

        for arg in node.args.args:
            hashed = self.hashed_random_string()
            self.mapping[arg.arg] = hashed
            arg.arg = hashed

        for decorator in node.decorator_list:
            if type(decorator) == ast.Call:
                unparsed = ast.unparse(decorator.func).split(".")
                if new_name := self.rename(unparsed[0]):
                    new = f"{new_name}.{'.'.join(i for i in unparsed[1:])}"
                    decorator.func = ast.Name(id=new)

        for line in node.body:
            self.in_function = True
            self.visit(line)
            self.in_function = False

        return node

    def visit_ClassDef(self, node):
        if new_name := self.rename(node.name):
            node.name = new_name

        self.current_class_name = node.name
        for base in node.bases:
            self.visit(base)

        for line in node.body:
            self.visit(line)

        self.current_class_name = False
        return node

    def visit_Call(self, node):
        # call.func
        if isinstance(node.func, ast.Attribute):
            if node.lineno not in (0,1):
                node.func = self.visit(node.func)
            else:
                self.visit(node.func)
        else:
            self.visit(node.func)

        # call.args
        node.args = [self.visit(arg) for arg in node.args]

        # call.keywords
        node.keywords = [self.visit(keyword) for keyword in node.keywords]
        return node

    def visit_keyword(self, node):
        # if new_name := self.rename(node.arg):
        #     node.arg = new_name
        node.value = self.visit(node.value)
        return node

    def visit_Assign(self, node):
        if self.current_class_name and not self.in_function:
            node.value = self.visit(node.value)
            return node

        node.value = self.visit(node.value)
        node.targets = [self.visit(target) for target in node.targets]
        return node

    def visit_Name(self, node):
        if new_name := self.rename(node.id):
            node.id = new_name
        return node

    def visit_Attribute(self, node):
        self.visit(node.value)

        if isinstance(node.ctx, ast.Load) and maximize_protection:
            if node.attr.startswith('__'):
                print(node.attr, self.current_class_name)
                compare_call = ast.Call(func=ast.Name(id=self.rename("getattr"), ctx=ast.Load()), args=[node.value, ast.Constant(value=f"_{self.current_class_name}{node.attr}")], keywords=[])
            else:
                encoded = Helpers.encode_string(node.attr)
                decode_call = ast.Call(func=ast.Name(id=self.rename('decode_string'), ctx=ast.Load()), args=[ast.Constant(value=encoded)], keywords=[])
                compare_call = ast.Call(func=ast.Name(id=self.rename("getattr"), ctx=ast.Load()), args=[node.value, decode_call], keywords=[])
            return compare_call

        return node

    def visit_Delete(self, node):
        new_nodes = []

        for target in node.targets:
            if isinstance(target, ast.Attribute):
                obj = self.visit(target.value)

                if target.attr.startswith('__'):
                    encoded = Helpers.encode_string(f"_{self.current_class_name}{target.attr}")
                else:
                    encoded = Helpers.encode_string(target.attr)

                decode_call = ast.Call(func=ast.Name(id=self.rename('decode_string'), ctx=ast.Load()), args=[ast.Constant(value=encoded)], keywords=[])
                delattr_call = ast.Expr(value=ast.Call(func=ast.Name(id=self.rename('delattr'), ctx=ast.Load()), args=[obj, decode_call], keywords=[]))
                new_nodes.append(delattr_call)
            else:
                new_nodes.append(ast.Delete(targets=[self.visit(target)]))  # Keep non-attribute targets as Delete

        return new_nodes

    def visit_arguments(self, node):
        for arg in node.args:
            if new_name := self.rename(arg.arg):
                arg.arg = new_name
            if arg.annotation:
                node.annotation = self.visit(arg.annotation)
        return node

    def visit_Compare(self, node):
        ast_comparitors = [ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Is, ast.IsNot, ast.In, ast.NotIn]
        compare_ops = {ast_compare: func_compare for ast_compare, func_compare in zip(ast_comparitors, self.compare_ops)}

        if len(node.ops) == 1:
            compare_op = compare_ops.get(type(node.ops[0]))
            compare_call = ast.Call(func=ast.Name(id=self.rename(compare_op), ctx=ast.Load()), args=[self.visit(node.left), self.visit(node.comparators[0])], keywords=[])
            return compare_call
        return node

class Indent_Mask():
    def __init__(self, content, builtins_scramble):
        self.new_content = ""
        self.builtins_scramble = builtins_scramble
        self.non_call_builtins = ['__name__', '__doc__', '__package__', '__loader__', '__spec__', 'abs', 'all', 'any', 'ascii', 'bin', 'breakpoint', 'callable', 'chr', 'compile', 'delattr', 'dir', 'divmod', 'eval', 'exec', 'format', 'getattr', 'globals', 'hasattr', 'hash', 'hex', 'id', 'input', 'isinstance', 'issubclass', 'iter', 'aiter', 'len', 'locals', 'max', 'min', 'next', 'anext', 'oct', 'ord', 'pow', 'print', 'repr', 'round', 'setattr', 'sorted', 'sum', 'vars', 'None', 'Ellipsis', 'NotImplemented', 'False', 'True', 'bool', 'memoryview', 'bytearray', 'bytes', 'classmethod', 'complex', 'dict', 'enumerate', 'filter', 'float', 'frozenset', 'property', 'int', 'list', 'map', 'object', 'range', 'reversed', 'set', 'slice', 'staticmethod', 'str', 'super', 'tuple', 'type', 'zip', 'BaseException', 'Exception', 'TypeError', 'StopAsyncIteration', 'StopIteration', 'GeneratorExit', 'SystemExit', 'KeyboardInterrupt', 'ImportError', 'ModuleNotFoundError', 'OSError', 'EnvironmentError', 'IOError', 'WindowsError', 'EOFError', 'RuntimeError', 'RecursionError', 'NotImplementedError', 'NameError', 'UnboundLocalError', 'AttributeError', 'SyntaxError', 'IndentationError', 'TabError', 'LookupError', 'IndexError', 'KeyError', 'ValueError', 'UnicodeError', 'UnicodeEncodeError', 'UnicodeDecodeError', 'UnicodeTranslateError', 'AssertionError', 'ArithmeticError', 'FloatingPointError', 'OverflowError', 'ZeroDivisionError', 'SystemError', 'ReferenceError', 'MemoryError', 'BufferError', 'Warning', 'UserWarning', 'EncodingWarning', 'DeprecationWarning', 'PendingDeprecationWarning', 'SyntaxWarning', 'RuntimeWarning', 'FutureWarning', 'ImportWarning', 'UnicodeWarning', 'BytesWarning', 'ResourceWarning', 'ConnectionError', 'BlockingIOError', 'BrokenPipeError', 'ChildProcessError', 'ConnectionAbortedError', 'ConnectionRefusedError', 'ConnectionResetError', 'FileExistsError', 'FileNotFoundError', 'IsADirectoryError', 'NotADirectoryError', 'InterruptedError', 'PermissionError', 'ProcessLookupError', 'TimeoutError', 'open', 'quit', 'exit', 'copyright', 'credits', 'license', 'help']
        for builtin in self.non_call_builtins:
            if builtin not in self.builtins_scramble:
                print(builtin)

        self.obfuscate(content)

    def indentation(self, s, tabsize=4):
        sx = s.expandtabs(tabsize)
        return 0 if sx.isspace() else len(sx) - len(sx.lstrip())

    def obfuscate(self, content):
        for line in content.splitlines():
            if line[0] == "@" or line[0] == '"' or line[0] == "'" or "#" in line or ":" in line:
                pass
            elif line.startswith(" ") or line.startswith("	"):
                tab = " "*self.indentation(line)
                line_no_indent = textwrap.dedent(line)
                random_builtins = f"{self.builtins_scramble[random.choice(self.non_call_builtins)]}{' ' * random.randint(min_indent_space, min_indent_space*2)};" * random.randint(20, 50)
                line = f"{tab}{random_builtins[:-1]}{' ' * random.randint(min_indent_space*5, min_indent_space*10)};{line_no_indent}"
            else:
                random_builtins = f"{self.builtins_scramble[random.choice(self.non_call_builtins)]}{' ' * random.randint(min_indent_space, min_indent_space*2)};" * random.randint(20, 50)
                line = f"{random_builtins[:-1]}{' ' * random.randint(min_indent_space*5, min_indent_space*10)};{line}"

            self.new_content += line + "\n"


if __name__ == "__main__":
    decode_str_lambda = "decode_string = lambda encoded_string: ''.join([char if (encoded_string[i-1] == '𑻠') else unicode_dict[char] for i, char in enumerate(encoded_string) if char in unicode_dict])"

    file_path = input("Input a filepath or leave empty for to_obfuscate.py") or "to_obfuscate.py"
    with open(file_path, "r", encoding="unicode_escape") as f:
        content = f.read()

    # Removing Docstrings, Comments etc
    single_line_comment_pattern = r'#.*?$'
    code = re.sub(single_line_comment_pattern, '', content, flags=re.MULTILINE)
    # Regular expression to match multi-line comments and docstrings
    multi_line_comment_pattern = r'(\'\'\'(.*?)\'\'\'|\"\"\"(.*?)\"\"\")'
    code = re.sub(multi_line_comment_pattern, '', code, flags=re.MULTILINE | re.DOTALL)
    # Remove empty lines resulting from the removal of comments and docstrings
    content = "\n".join([line for line in code.splitlines() if line.strip()])

    # Replacing Tabs with spaces
    content = content.replace('\t', '    ')

    value_obfuscator = ValueObfuscator()
    tree = ast.parse(content, type_comments=True)
    value_obfuscator.visit(tree)
    content = ast.unparse(tree)

    if len(content) == 0:
        exit("No obfuscatable code found.")

    content = decode_str_lambda + "\n" + content
    tree = ast.parse(content, type_comments=True)
    constant_obfuscator = ConstantObfuscator()
    constant_obfuscator.visit(tree)
    content = ast.unparse(tree)

    # content = decode_lambda.split(".bit_length()")[0] + ".bit_length()" + decode_str_lambda_part2 + "\n" + content_not_decode_lambda
    content = python_minifier.minify(content, rename_locals=False, rename_globals=False, hoist_literals=False, preserve_shebang=False)

    # Add Builtins
    assignments = ",".join(list(constant_obfuscator.builtins_scramble.values()))
    real_builtins = ",".join(list(constant_obfuscator.builtins_scramble.keys()))
    content = f"{assignments}={real_builtins}\n"+content

    # Indent Masking
    if indent_masking:
        indent_mask = Indent_Mask(content, constant_obfuscator.builtins_scramble)
        content = indent_mask.new_content

    # Replacing Tabs with spaces
    content = content.replace('\t', '    ')

    print("----------------------New Content------------------------")
    print(content)
    pyperclip.copy(content)
    print("Copied to Clipboard!")

    with open("obfuscated.py", "w", encoding="utf-8") as f:
        f.write(content)

