import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import re
import pandas as pd
import plotly.express as px
from datetime import datetime
from collections import Counter

st.set_page_config(page_title="Loto Kombinasyon Üretici", page_icon="🍀", layout="wide")

st.markdown("""
<style>
.ball-row { display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin:3px 0; }
.ball { width:42px; height:42px; border-radius:50%; display:flex; align-items:center;
        justify-content:center; font-weight:700; font-size:14px; color:#fff; flex-shrink:0; }
.sep  { font-size:20px; color:#bbb; margin:0 2px; }
.row-label { font-size:12px; color:#888; margin-bottom:1px; font-weight:500; }
.info-note { font-size:11px; color:#aaa; font-style:italic; margin-top:6px; }
</style>
""", unsafe_allow_html=True)

# ─── On Numara geçmiş çekiliş verisi ─────────────────────────────────────────
ON_NUMARA_ARSIV_RAW = """40	18/05/2026	2	5	8	16	19	24	27	32	38	39	42	44	48	52	63	64	66	68	74	75	78	79
39	15/05/2026	3	9	10	13	16	18	31	35	37	40	43	44	45	48	52	54	58	63	64	66	70	73
38	11/05/2026	1	2	6	13	17	21	24	27	33	38	39	43	48	56	60	61	62	66	70	74	76	80
37	08/05/2026	6	12	14	15	18	19	24	27	29	31	40	42	50	53	59	61	62	63	71	72	74	77
36	04/05/2026	1	10	11	13	14	17	19	20	24	28	32	33	46	48	52	58	59	60	65	69	72	79
35	01/05/2026	3	11	12	14	16	17	23	25	27	29	37	39	42	49	50	54	56	58	59	61	63	71
34	27/04/2026	5	7	8	11	14	18	24	27	31	40	46	47	48	50	51	56	59	61	62	64	66	67
33	24/04/2026	8	11	15	16	18	33	36	37	49	52	55	56	58	63	64	66	67	68	72	75	76	79
32	20/04/2026	5	7	18	25	27	28	31	32	34	35	38	50	52	55	60	61	67	69	73	75	78	79
31	17/04/2026	1	5	8	9	10	16	23	25	26	33	37	38	48	52	53	56	58	61	64	70	77	78
30	13/04/2026	1	2	8	9	20	25	27	29	36	37	41	49	53	54	55	57	62	65	68	72	74	77
29	10/04/2026	3	6	7	9	12	15	17	18	20	24	25	31	33	37	40	41	46	49	53	57	60	77
28	06/04/2026	3	7	9	18	21	27	29	36	39	42	45	54	55	59	61	69	73	74	76	77	79	80
27	03/04/2026	5	6	9	16	20	21	26	27	28	30	38	46	48	50	53	54	56	66	67	69	79	80
26	30/03/2026	2	3	8	10	11	12	18	20	21	25	28	35	37	38	46	51	55	63	68	72	75	79
25	27/03/2026	2	7	9	17	25	32	34	35	41	43	46	51	52	53	58	59	67	68	71	75	78	79
24	23/03/2026	2	12	14	16	19	23	26	31	33	34	36	38	43	52	56	57	61	66	69	70	72	78
23	20/03/2026	4	7	8	12	18	19	22	25	29	34	35	38	39	42	43	46	49	61	64	65	68	71
22	16/03/2026	6	10	16	23	28	31	34	36	37	38	39	42	45	49	50	57	63	65	66	71	76	79
21	13/03/2026	4	5	11	17	18	19	26	27	29	30	31	34	40	46	47	48	50	55	61	64	73	80
20	09/03/2026	1	5	11	13	16	17	24	28	31	39	41	46	50	52	55	62	66	70	72	77	79	80
19	06/03/2026	8	12	14	16	18	21	22	23	29	36	43	44	46	47	48	50	55	59	61	69	71	78
18	02/03/2026	6	9	18	23	28	32	35	36	42	45	46	47	52	54	55	56	61	68	70	73	78	79
17	27/02/2026	1	2	7	8	9	11	23	27	28	30	32	39	51	58	64	67	70	73	75	76	79	80
16	23/02/2026	2	3	6	7	15	16	25	26	30	31	36	38	39	41	50	53	62	74	75	76	77	79
15	20/02/2026	10	11	12	19	22	27	29	31	35	44	45	47	48	51	58	63	69	70	71	72	75	77
14	16/02/2026	5	12	13	19	20	22	24	34	36	37	40	41	46	55	56	62	67	68	70	74	78	80
13	13/02/2026	3	6	9	11	19	26	28	29	32	37	39	40	42	49	51	60	61	64	66	68	69	73
12	09/02/2026	2	3	4	6	9	16	17	18	21	37	39	41	42	43	50	61	62	63	69	76	77	79
11	06/02/2026	2	7	13	14	15	25	29	32	40	48	50	59	65	66	67	70	71	72	76	77	79	80
10	02/02/2026	10	11	13	18	19	20	21	26	27	32	34	39	42	45	49	54	60	61	67	68	69	73
9	30/01/2026	2	5	12	15	16	21	23	25	28	34	36	37	38	49	51	57	58	60	61	71	76	79
8	26/01/2026	9	11	12	13	17	19	20	22	24	25	28	31	36	40	41	45	58	60	61	67	73	79
7	23/01/2026	3	6	14	16	20	21	28	29	31	32	35	45	48	54	56	64	65	66	70	71	72	80
6	19/01/2026	4	17	22	23	24	27	28	32	33	38	48	55	58	60	63	69	70	71	72	73	76	78
5	16/01/2026	1	4	10	13	14	25	31	35	41	42	43	44	46	47	50	51	54	58	59	67	71	73
4	12/01/2026	1	4	5	7	11	12	16	18	19	33	38	41	44	46	54	59	60	61	63	64	67	68
3	09/01/2026	5	21	27	28	29	37	40	49	54	55	57	60	61	62	66	67	68	69	72	74	77	80
2	05/01/2026	2	9	18	20	21	22	24	31	36	39	40	43	45	50	54	56	64	70	72	74	76	80
1	02/01/2026	3	7	9	15	18	21	23	25	27	28	29	45	46	51	55	56	58	59	71	74	75	76
104	29/12/2025	10	11	20	22	24	26	31	36	38	40	47	49	51	55	58	61	63	64	67	70	78	79
103	26/12/2025	5	15	17	19	24	25	31	38	40	43	45	50	52	53	60	63	65	66	74	75	76	79
102	22/12/2025	2	4	5	7	9	11	12	21	26	27	29	37	39	46	50	56	57	59	63	65	71	76
101	19/12/2025	1	3	4	11	17	22	26	28	33	35	40	44	48	50	55	57	64	67	70	71	72	78
100	15/12/2025	9	10	12	20	23	27	30	33	39	41	45	52	53	54	57	64	68	69	72	75	76	78
99	12/12/2025	2	10	12	13	14	17	21	24	27	28	30	32	34	36	44	45	50	63	65	70	76	77
98	08/12/2025	6	9	15	18	23	26	28	30	31	46	47	49	54	60	61	65	69	70	71	74	77	79
97	05/12/2025	1	3	4	5	8	9	10	20	23	24	25	28	29	34	50	64	65	69	76	77	79	80
95	28/11/2025	1	4	8	12	16	22	24	30	32	33	34	35	37	38	40	50	53	56	59	60	66	72
94	24/11/2025	1	2	7	8	10	13	14	21	27	29	31	39	43	56	61	62	63	67	68	69	72	76
93	21/11/2025	3	4	8	24	26	28	29	31	32	34	36	43	44	46	51	54	56	63	74	78	79	80
92	17/11/2025	3	4	6	8	11	15	21	23	29	30	31	45	47	52	53	54	56	59	70	71	78	79
91	14/11/2025	1	2	7	18	24	32	38	45	46	51	52	53	55	58	61	62	65	67	69	72	73	75
90	10/11/2025	1	2	3	9	10	11	15	17	19	24	27	32	42	44	45	46	47	50	55	57	62	65
89	07/11/2025	2	3	7	8	21	22	25	32	34	38	40	44	46	47	52	53	54	55	56	61	62	65
88	03/11/2025	5	20	21	25	26	27	29	33	36	38	39	41	42	46	57	59	61	69	72	76	79	80
87	31/10/2025	1	2	4	15	21	24	26	32	36	42	43	44	45	48	51	53	54	62	73	75	80
86	27/10/2025	1	3	4	6	12	19	21	22	23	33	34	38	41	42	47	48	53	60	63	70	73	77
85	24/10/2025	5	12	16	17	18	20	22	23	36	50	52	53	54	57	59	60	61	72	73	74	76	78
84	20/10/2025	8	11	14	16	17	20	21	23	26	30	44	47	60	61	64	65	68	70	71	72	75	80
83	17/10/2025	1	12	13	16	26	27	28	29	35	36	37	38	45	48	58	59	60	63	68	73	78	80
82	13/10/2025	2	5	6	9	10	12	14	24	25	27	30	37	42	44	47	48	55	63	73	77	78	80
81	10/10/2025	1	3	4	9	13	28	31	34	39	40	50	54	57	59	63	64	66	67	70	76	77	79
80	06/10/2025	1	7	9	10	16	20	27	28	39	43	53	55	59	60	65	67	69	70	71	75	76	80
79	03/10/2025	2	9	14	17	23	24	26	30	32	37	39	45	46	47	56	57	59	60	64	65	66	74
78	29/09/2025	2	3	4	7	9	11	16	18	28	33	35	45	49	50	59	64	65	67	68	69	70	78
77	26/09/2025	3	11	15	18	22	27	30	36	40	44	49	51	52	53	54	56	67	69	70	71	74	76
76	22/09/2025	3	5	9	21	22	30	36	40	41	46	47	51	58	60	61	63	64	67	69	74	78	79
75	19/09/2025	2	4	9	13	16	22	24	28	29	31	36	40	43	49	50	52	53	55	64	69	75	76
74	15/09/2025	3	5	10	11	13	14	15	16	25	28	32	33	41	45	53	62	63	64	66	67	69	75
73	12/09/2025	24	26	27	29	31	32	35	36	37	38	47	51	58	60	63	71	74	75	76	77	78	80
72	08/09/2025	7	9	10	12	18	19	20	24	31	38	43	45	46	47	52	56	57	59	62	71	73	78
71	05/09/2025	1	2	6	10	23	29	30	35	38	40	41	44	47	49	55	56	58	59	66	67	71	72
70	01/09/2025	3	4	10	12	14	15	27	34	40	41	46	49	53	58	59	60	71	73	75	76	77	79
69	29/08/2025	2	4	5	6	7	10	16	20	23	28	30	33	49	53	64	68	70	71	72	73	79	80
68	25/08/2025	2	5	8	9	12	14	18	23	25	26	32	38	44	50	53	55	56	58	62	65	66	68
67	22/08/2025	1	7	8	14	17	22	35	40	41	45	47	54	57	59	60	63	68	69	70	72	74	80
66	18/08/2025	1	2	3	4	10	15	21	24	29	30	31	32	33	35	40	43	50	57	59	68	71	75
65	15/08/2025	1	6	9	16	17	32	33	36	37	41	53	55	56	58	59	60	63	64	68	75	80
64	11/08/2025	1	5	16	17	18	24	25	30	31	34	38	40	44	49	51	55	56	60	61	67	72	78
63	08/08/2025	2	6	14	17	18	21	33	34	38	40	44	48	51	52	54	58	60	61	68	72
62	04/08/2025	4	11	12	15	17	19	25	29	32	37	39	40	43	47	48	50	57	59	61	67	69	78
61	01/08/2025	7	9	10	12	13	16	18	21	27	34	40	41	47	48	54	57	63	66	70	72	74	80
60	28/07/2025	2	4	5	11	12	13	15	18	19	26	28	30	37	41	42	44	48	53	60	68	76	80
59	25/07/2025	4	7	16	19	24	25	26	27	29	30	31	36	37	40	42	50	56	59	60	70	72	75
58	21/07/2025	5	6	8	9	10	11	14	17	20	22	25	28	32	34	39	42	45	52	68	70	76	78
57	18/07/2025	1	4	6	7	11	14	15	16	21	27	31	32	43	45	47	50	52	54	63	66	75	77
56	14/07/2025	1	7	8	11	18	21	24	27	28	38	41	42	43	55	65	67	70	73	75	76	78	80
55	11/07/2025	4	11	12	16	22	28	31	32	34	35	43	47	48	49	52	54	60	64	66	72	76	79
54	07/07/2025	5	8	13	14	20	21	26	27	34	38	40	47	52	54	58	62	63	65	66	70	74	77
53	04/07/2025	6	10	14	17	19	22	26	29	30	35	36	42	50	58	67	68	71	72	74	75	78	80
52	30/06/2025	1	11	18	19	21	22	32	33	34	35	38	42	45	47	52	54	58	59	62	63	71	79
51	27/06/2025	2	9	11	12	24	30	33	34	35	41	42	50	52	53	55	57	65	66	69	77	78	79
50	23/06/2025	4	5	6	7	23	25	28	31	33	36	40	41	43	46	47	54	58	59	62	64	70	79
49	20/06/2025	1	3	4	14	15	22	24	27	28	31	35	39	41	43	44	50	57	58	60	62	75	78
48	16/06/2025	4	6	7	8	11	15	23	26	27	34	41	42	45	57	58	61	64	66	68	69	72	79
47	13/06/2025	1	3	13	23	24	27	28	29	30	31	35	38	39	44	55	60	66	68	71	75	77	80
46	09/06/2025	6	10	13	21	24	25	26	27	28	29	35	38	43	46	48	49	55	56	58	62	66	80
45	06/06/2025	15	16	17	20	21	25	26	28	34	37	40	42	53	54	58	60	62	64	67	68	74	75
44	02/06/2025	5	12	14	16	23	27	31	36	38	39	43	45	46	55	58	59	60	69	70	74	77	79
43	30/05/2025	3	4	8	9	12	19	24	28	31	32	34	39	45	49	54	56	58	65	67	68	72	75
42	26/05/2025	1	5	9	10	12	14	19	22	28	34	38	40	42	45	55	58	74	75	76	77	79	80
41	23/05/2025	4	6	8	11	12	21	22	24	28	30	31	39	41	45	50	54	64	70	71	74	76	79
40	19/05/2025	2	3	5	15	19	26	33	42	45	46	47	48	51	52	57	59	61	64	65	67	69	73
39	16/05/2025	9	13	14	28	29	38	39	40	41	42	43	49	52	56	59	62	65	68	71	72	73	80
38	12/05/2025	4	5	6	22	24	25	27	32	38	41	42	45	48	51	54	56	58	59	61	73	78	79
37	09/05/2025	2	6	8	9	15	16	17	20	21	36	37	46	50	52	53	56	58	62	63	68	70	80
36	05/05/2025	2	5	10	15	17	19	22	24	29	39	40	48	49	52	53	56	71	72	74	75	77	80
35	02/05/2025	1	3	4	9	10	15	20	22	23	28	33	43	44	45	52	56	57	60	67	75	78	80
34	28/04/2025	1	6	10	17	21	23	24	27	28	31	36	38	42	46	49	52	64	65	67	68	72	75
33	25/04/2025	10	13	14	16	18	22	28	32	38	40	41	42	45	50	56	65	66	73	74	75	77
32	21/04/2025	4	7	11	15	20	22	25	26	28	29	37	40	41	56	62	63	68	69	71	72	73	80
31	18/04/2025	2	10	12	17	21	24	27	29	32	36	37	40	41	42	43	47	54	66	72	74	75	80
30	14/04/2025	1	4	12	14	17	19	24	25	26	27	28	37	38	41	46	48	50	52	54	69	72	73
29	11/04/2025	2	4	7	9	10	12	14	19	24	32	33	38	40	48	49	51	53	62	64	72	74	76
28	07/04/2025	2	5	17	20	22	26	29	33	42	43	44	49	54	56	61	68	69	70	72	73	74	77
27	04/04/2025	1	2	4	6	8	9	13	16	28	29	35	38	43	48	50	59	63	73	75	77	78	80
26	31/03/2025	2	9	11	12	13	16	23	27	28	29	31	34	38	41	56	57	63	64	73	75	79	80
25	28/03/2025	2	4	14	16	17	22	23	27	29	35	38	40	44	51	54	55	57	63	69	70	77	80
24	24/03/2025	1	2	3	9	13	15	16	17	28	29	30	31	43	44	47	48	50	54	58	73	76	78
23	21/03/2025	4	5	18	20	32	33	35	37	38	46	51	54	57	64	65	67	68	70	71	72	75	78
22	17/03/2025	1	3	6	7	10	12	15	20	31	36	38	42	50	54	58	60	62	69	73	76	78	79
21	14/03/2025	4	8	9	10	14	18	19	26	29	31	32	38	40	47	54	58	68	70	72	73	74	80
20	10/03/2025	2	4	14	17	24	27	31	37	39	40	45	51	53	54	55	60	61	64	65	70	74	77
19	07/03/2025	4	6	7	8	10	14	18	19	20	28	29	38	39	48	55	56	57	59	65	69	71	73
18	03/03/2025	1	3	5	6	9	10	11	13	17	23	24	30	32	47	48	55	63	64	67	71	74	79
17	28/02/2025	2	5	6	8	11	18	22	23	26	30	39	41	44	47	50	53	56	62	67	75	77	79
16	24/02/2025	6	8	9	10	17	21	24	29	32	35	36	40	49	51	55	58	62	65	66	70	72	74
15	21/02/2025	2	4	6	8	20	22	27	29	30	31	34	37	39	40	41	52	53	57	62	67	71	72
14	17/02/2025	6	8	9	31	33	34	46	47	49	52	55	56	57	58	63	64	66	71	72	76	77	79
13	14/02/2025	1	5	10	11	12	15	19	25	26	31	38	43	44	49	51	52	55	57	59	61	65	76
12	10/02/2025	8	10	11	12	15	16	21	24	25	29	31	32	34	35	42	44	45	55	65	73	74	80
11	07/02/2025	5	7	12	14	16	18	26	28	33	34	37	45	47	51	55	58	63	65	66	67	76	77
10	03/02/2025	1	4	8	17	18	23	24	34	40	41	46	48	50	51	54	55	57	64	67	68	69	70
9	31/01/2025	2	5	7	12	14	15	21	22	27	28	30	35	41	58	59	62	64	66	67	72	78	80
8	27/01/2025	2	7	10	16	22	25	26	33	34	35	37	38	42	44	47	48	51	52	58	63	66	69
7	24/01/2025	7	14	15	20	21	24	25	27	30	35	42	44	51	52	56	57	59	63	72	73	77	79
6	20/01/2025	5	7	12	13	14	15	19	20	25	26	28	38	42	46	51	63	65	67	70	71	75	77
5	17/01/2025	4	6	11	12	20	23	24	25	29	31	34	38	40	43	45	47	48	58	61	63	70	77
4	13/01/2025	2	3	4	5	10	15	19	20	29	32	33	39	40	44	47	51	57	60	66	67	73	80
3	10/01/2025	4	9	12	13	15	22	23	25	26	34	35	41	45	48	49	50	54	57	59	63	74	75
2	06/01/2025	5	7	8	10	13	18	19	21	24	25	31	35	39	41	43	49	55	56	64	71	72	79
1	03/01/2025	2	13	14	19	25	26	27	31	35	41	43	47	54	56	57	58	61	62	63	64	70	71"""

def parse_arsiv(raw: str):
    rows = []
    for line in raw.strip().split('\n'):
        parts = line.split('\t')
        if len(parts) < 3:
            continue
        try:
            hafta = int(parts[0])
            tarih = parts[1]
            sayilar = []
            for x in parts[2:]:
                try:
                    n = int(x)
                    if 1 <= n <= 80 and n not in sayilar:
                        sayilar.append(n)
                except:
                    pass
            if sayilar:
                rows.append({"hafta": hafta, "tarih": tarih, "sayilar": sayilar})
        except:
            pass
    rows.sort(key=lambda r: r["hafta"], reverse=True)
    return rows

ON_NUMARA_ARSIV = parse_arsiv(ON_NUMARA_ARSIV_RAW)

# ─── Yedek istatistik verisi ──────────────────────────────────────────────────
YEDEK = {
    "Sayisal-Loto": {
        "sicak": [(45,82),(87,80),(71,79),(62,73),(60,73),(89,72),(18,72),(56,71),(38,71),(88,70),
                  (23,69),(69,69),(13,69),(12,67),(5,67),(64,67),(1,67),(8,67),(63,66),(80,66),
                  (46,66),(41,66),(77,66),(6,65),(47,65),(48,64),(66,64),(7,64),(50,63),(40,63)],
        "soguk": [(54,67),(85,59),(51,44),(73,40),(15,39),(49,38),(21,33),(22,33),(65,32),(58,32),
                  (44,31),(57,28),(32,27),(46,27),(77,27),(61,26),(86,25),(71,24),(20,23),(67,23)],
    },
    "Super-Loto": {
        "sicak": [(44,22),(41,20),(7,18),(9,18),(3,17),(21,17),(55,17),(32,16),(36,16),(6,15),
                  (16,15),(19,15),(37,15),(47,14),(52,14),(14,13),(23,13),(34,13),(38,13),(51,13)],
        "soguk": [(13,49),(58,37),(10,34),(15,33),(4,31),(53,25),(18,23),(59,21),(40,19),(24,19),
                  (45,18),(30,16),(20,15),(26,15),(17,14),(28,14),(49,13),(60,13),(22,12),(27,12)],
    },
    "Sans-Topu": {
        "sicak": [(5,99),(2,98),(22,98),(18,96),(6,96),(14,95),(29,94),(7,94),(8,93),(26,91),
                  (25,91),(12,90),(21,90),(33,90),(32,89),(23,89),(34,89),(15,88),(1,87),(3,86)],
        "soguk": [(31,18),(10,15),(4,14),(17,12),(30,11),(3,10),(28,9),(13,8),(19,8),(1,7),
                  (20,7),(27,7),(9,6),(16,6),(24,6),(11,5),(2,4),(5,4),(8,4),(22,4)],
        "bonus_sicak": [(2,38),(8,36),(11,35),(6,34),(14,34),(1,33),(4,33),(7,32),(13,31),(3,30)],
        "bonus_soguk": [(12,8),(5,7),(10,7),(3,6),(9,6),(14,5),(1,4),(4,4),(6,4),(7,4)],
    },
    "On-Numara": {
        "sicak": [(77,195),(16,193),(2,189),(4,188),(50,187),(53,184),(12,183),(27,183),(28,179),
                  (60,177),(65,177),(52,177),(57,176),(73,175),(79,175),(48,174),(55,173),(40,173),
                  (6,173),(47,171),(31,171),(13,170),(71,168),(11,168),(18,168),(15,167),(37,167),
                  (34,167),(58,166),(32,166)],
        "soguk": [(22,18),(4,18),(30,14),(57,11),(41,11),(26,10),(34,9),(55,8),(36,8),(51,7),
                  (67,7),(7,7),(47,7),(49,6),(25,6),(23,6),(28,5),(46,5),(11,5),(20,5)],
    },
}

OYUNLAR = {
    "🎯 Sayısal Loto": {"slug":"Sayisal-Loto","havuz":90,"secim":6,"bonus":False,"renk":"#1a4fa0","aciklama":"1–90 arası 6 sayı","olasilik":"1 / 622.614.630"},
    "⭐ Süper Loto":   {"slug":"Super-Loto",  "havuz":60,"secim":6,"bonus":False,"renk":"#7d3c98","aciklama":"1–60 arası 6 sayı","olasilik":"1 / 50.063.860"},
    "🔵 Şans Topu":   {"slug":"Sans-Topu",   "havuz":34,"secim":5,"bonus":True, "bonus_havuz":14,"bonus_renk":"#e6a817","renk":"#16a085","aciklama":"1–34 arası 5 sayı + Şans Topu (1–14)","olasilik":"1 / 3.895.584"},
    "🔴 On Numara":   {"slug":"On-Numara",   "havuz":80,"secim":10,"bonus":False,"renk":"#c0392b","aciklama":"1–80 arası 10 sayı (22 çekilir)","olasilik":"1 / 2.545.786"},
}

# ─── Scraper ──────────────────────────────────────────────────────────────────
def parse_numred(url):
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        for img in soup.find_all("img", src=re.compile(r"img/num/\d+\.png|NumRed/\d+\.png")):
            m = re.search(r"/(\d+)\.png", img["src"])
            if not m:
                continue
            num = int(m.group(1))
            td = img.find_parent("td")
            if td:
                sib = td.find_next_sibling("td")
                if sib:
                    vm = re.search(r"\d+", sib.get_text())
                    if vm:
                        results.append((num, int(vm.group())))
        return results
    except:
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def veri_yukle(slug):
    base = "https://www.lotokurdu.com"
    slug_map = {
        "Sayisal-Loto": ("Sayisal-Loto-En-Cok-Cikan-Sayilar","Sayisal-Loto-En-Uzun-Zamandir-Cikmayan-Sayilar"),
        "Super-Loto":   ("Super-Loto-En-Cok-Cikan-Sayilar","Super-Loto-En-Uzun-Zamandir-Cikmayan-Sayilar"),
        "Sans-Topu":    ("Sans-Topu-En-Cok-Cikan-Sayilar","Sans-Topu-En-Uzun-Zamandir-Cikmayan-Sayilar"),
        "On-Numara":    ("On-Numara-En-Cok-Cikan-Sayilar","On-Numara-En-Uzun-Zamandir-Cikmayan-Sayilar"),
    }
    s1, s2 = slug_map.get(slug, ("",""))
    sicak = parse_numred(f"{base}/{s1}")
    soguk = parse_numred(f"{base}/{s2}")
    yedek = YEDEK.get(slug, {})
    kaynak = "lotokurdu.com" if sicak else "yedek veri"
    if not sicak: sicak = yedek.get("sicak", [])
    if not soguk: soguk = yedek.get("soguk", [])
    return sicak, soguk, yedek.get("bonus_sicak",[]), yedek.get("bonus_soguk",[]), kaynak

# ─── Son çekilişlere dayalı mod ───────────────────────────────────────────────
def son_cekilis_mod(arsiv, n_cekilis, secim=10, aday_sayisi=30):
    son_n = arsiv[:n_cekilis]
    tum = []
    for row in son_n:
        tum.extend(row["sayilar"])
    freq = Counter(tum)
    adaylar = [num for num, _ in freq.most_common(aday_sayisi)]
    if len(adaylar) < secim:
        adaylar += [x for x in range(1,81) if x not in adaylar]
    return sorted(random.sample(adaylar[:aday_sayisi], min(secim, len(adaylar)))), freq, son_n

# ─── Kombinasyon üretici ──────────────────────────────────────────────────────
def uret(mod, havuz, secim, sicak, soguk):
    sn = [x for x,_ in sicak if 1<=x<=havuz]
    gn = [x for x,_ in soguk if 1<=x<=havuz]
    if mod == "Rastgele" or (not sn and not gn):
        return sorted(random.sample(range(1,havuz+1), secim))
    elif mod == "🔥 Sıcak":
        aday = sn[:max(secim*3,18)]
        if len(aday)<secim: aday += [x for x in range(1,havuz+1) if x not in aday]
        return sorted(random.sample(aday[:max(secim*2,14)], min(secim,len(aday))))
    elif mod == "❄️ Soğuk":
        aday = gn[:max(secim*3,18)]
        if len(aday)<secim: aday += [x for x in range(1,havuz+1) if x not in aday]
        return sorted(random.sample(aday[:max(secim*2,14)], min(secim,len(aday))))
    elif mod == "🎲 Karma":
        yarim=secim//2; diger=secim-yarim
        sa=sn[:20]; ga=[x for x in gn[:20] if x not in sa]
        if len(sa)<yarim: sa+=[x for x in range(1,havuz+1) if x not in sa]
        if len(ga)<diger: ga+=[x for x in range(1,havuz+1) if x not in ga and x not in sa]
        sec=(random.sample(sa[:max(yarim*2,10)],min(yarim,len(sa)))+
             random.sample(ga[:max(diger*2,10)],min(diger,len(ga))))
        return sorted(sec)
    return sorted(random.sample(range(1,havuz+1), secim))

def uret_bonus(mod, bh, bs, bg):
    if mod=="🔥 Sıcak" and bs:
        a=[x for x,_ in bs if 1<=x<=bh]; return random.choice(a[:6]) if a else random.randint(1,bh)
    elif mod=="❄️ Soğuk" and bg:
        a=[x for x,_ in bg if 1<=x<=bh]; return random.choice(a[:6]) if a else random.randint(1,bh)
    return random.randint(1,bh)

def mod_rengi(mod, varsayilan):
    return {"🔥 Sıcak":"#c0392b","❄️ Soğuk":"#16a085","🎲 Karma":"#7d3c98",
            "📅 Son Çekilişlere Dayalı":"#d35400"}.get(mod, varsayilan)

def toplar_html(nums, renk, bonus=None, bonus_renk="#e6a817"):
    html='<div class="ball-row">'
    for n in nums:
        html+=f'<div class="ball" style="background:{renk}">{n}</div>'
    if bonus is not None:
        html+=f'<div class="sep">+</div><div class="ball" style="background:{bonus_renk}">{bonus}</div>'
    html+='</div>'
    return html

def goster_grafik(data, baslik, renk, y_label):
    if not data: return
    df=pd.DataFrame(data,columns=["Sayı",y_label]).sort_values("Sayı")
    fig=px.bar(df,x="Sayı",y=y_label,title=baslik,color_discrete_sequence=[renk],height=250)
    fig.update_layout(margin=dict(t=36,b=10,l=10,r=10),plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",xaxis_title="",yaxis_title="")
    st.plotly_chart(fig,use_container_width=True)

def goster_top_listesi(data, renk, suffix, n=10):
    top=data[:n]
    if not top: return
    cols=st.columns(len(top))
    for col,(num,val) in zip(cols,top):
        col.markdown(f'<div style="text-align:center"><div class="ball" style="background:{renk};margin:0 auto 4px">{num}</div><div style="font-size:11px;color:#888">{val}{suffix}</div></div>',unsafe_allow_html=True)

# ─── Oyun sekmesi ─────────────────────────────────────────────────────────────
def oyun_sekmesi(cfg):
    slug=cfg["slug"]; havuz=cfg["havuz"]; secim=cfg["secim"]
    bonus=cfg["bonus"]; bonus_havuz=cfg.get("bonus_havuz",14)
    bonus_renk=cfg.get("bonus_renk","#e6a817"); renk=cfg["renk"]
    on_numara = slug == "On-Numara"

    with st.spinner("Veriler yükleniyor..."):
        sicak,soguk,b_sicak,b_soguk,kaynak = veri_yukle(slug)

    # Metrikler
    m1,m2,m3,m4=st.columns(4)
    m1.metric("Havuz",f"1–{havuz}")
    m2.metric("Seçim",f"{secim} sayı"+(" + şans topu" if bonus else ""))
    m3.metric("Büyük ikramiye",cfg["olasilik"])
    m4.metric("Veri kaynağı",kaynak)
    if kaynak=="yedek veri":
        st.warning("⚠️ lotokurdu.com'a bağlanılamadı — yedek istatistik verisi kullanılıyor.")
    st.divider()

    # Modlar
    modlar=["Rastgele","🔥 Sıcak","❄️ Soğuk","🎲 Karma"]
    if on_numara:
        modlar.append("📅 Son Çekilişlere Dayalı")

    c1,c2,c3=st.columns([3,1,1])
    with c1:
        mod=st.radio("Kombinasyon modu",modlar,horizontal=True,key=f"mod_{slug}")
    with c2:
        kolon=st.number_input("Kolon sayısı",1,20,5,key=f"kolon_{slug}")
    with c3:
        st.write(""); st.write("")
        uret_btn=st.button("🎯 Üret",key=f"uret_{slug}",use_container_width=True,type="primary")

    # Son çekilişlere dayalı slider
    n_cekilis = 5
    if on_numara and mod == "📅 Son Çekilişlere Dayalı":
        max_val = len(ON_NUMARA_ARSIV)
        n_cekilis = st.slider(
            f"Kaç son çekiliş baz alınsın? (Toplam {max_val} çekiliş mevcut)",
            min_value=3, max_value=min(30, max_val), value=5, step=1,
            key="slider_son_cekilis"
        )
        son_n_rows = ON_NUMARA_ARSIV[:n_cekilis]
        tarihler = f"{son_n_rows[-1]['tarih']} – {son_n_rows[0]['tarih']}"
        st.caption(f"📅 Baz alınan dönem: **{tarihler}** ({n_cekilis} çekiliş)")

    MOD_ACIK={
        "Rastgele":"Tüm sayılar eşit olasılıkla — tamamen şansa bırak.",
        "🔥 Sıcak":"Tüm zamanların en sık çıkan sayılarından oluşturulur.",
        "❄️ Soğuk":"En uzun süredir çıkmayan sayılardan oluşturulur.",
        "🎲 Karma":"Yarısı sıcak, yarısı soğuk sayılardan karma seçim.",
        "📅 Son Çekilişlere Dayalı":f"Son {n_cekilis} çekilişte en çok tekrar eden sayılar 30'a indirilir, oradan 10 seçilir.",
    }
    st.caption(f"ℹ️ {MOD_ACIK.get(mod,'')}")
    st.divider()

    # Üret
    if uret_btn:
        st.subheader("🎰 Kombinasyonlar")
        top_renk=mod_rengi(mod,renk)

        if on_numara and mod=="📅 Son Çekilişlere Dayalı":
            _, freq, son_n_rows = son_cekilis_mod(ON_NUMARA_ARSIV, n_cekilis, secim, 30)
            for i in range(kolon):
                nums,_,_ = son_cekilis_mod(ON_NUMARA_ARSIV, n_cekilis, secim, 30)
                st.markdown(f'<div class="row-label">Kolon {i+1}</div>',unsafe_allow_html=True)
                st.markdown(toplar_html(nums,top_renk),unsafe_allow_html=True)

            # 30 aday göster
            st.divider()
            tum=[]
            for row in ON_NUMARA_ARSIV[:n_cekilis]: tum.extend(row["sayilar"])
            freq=Counter(tum)
            adaylar=[num for num,_ in freq.most_common(30)]
            adaylar.sort()
            st.caption(f"**30 Aday Sayı** (son {n_cekilis} çekilişe göre):")
            aday_html='<div class="ball-row">'
            for n in adaylar:
                aday_html+=f'<div class="ball" style="background:{top_renk};width:36px;height:36px;font-size:12px">{n}</div>'
            aday_html+='</div>'
            st.markdown(aday_html,unsafe_allow_html=True)
        else:
            for i in range(kolon):
                nums=uret(mod,havuz,secim,sicak,soguk)
                bon=uret_bonus(mod,bonus_havuz,b_sicak,b_soguk) if bonus else None
                st.markdown(f'<div class="row-label">Kolon {i+1}</div>',unsafe_allow_html=True)
                st.markdown(toplar_html(nums,top_renk,bon,bonus_renk),unsafe_allow_html=True)

        st.divider()
        st.success("Hayırlısı olsun! 🍀")
        st.markdown('<p class="info-note">Not: İstatistik bazlı seçim matematiksel kazanma olasılığını değiştirmez.</p>',unsafe_allow_html=True)

    # İstatistikler
    with st.expander("📊 İstatistikleri Göster / Gizle",expanded=False):
        if on_numara:
            t1,t2,t3=st.tabs(["🔥 En Çok Çıkanlar","❄️ En Uzun Çıkmayanlar","📅 Arşiv Özeti"])
        else:
            t1,t2=st.tabs(["🔥 En Çok Çıkanlar","❄️ En Uzun Çıkmayanlar"])
            t3=None

        with t1:
            goster_top_listesi(sicak,renk,"×",n=12)
            goster_grafik(sicak,"Çıkma Sayısı",renk,"Çıkma")
        with t2:
            goster_top_listesi(soguk,"#16a085"," çekiliş",n=12)
            goster_grafik(soguk,"Çıkmama Süresi (çekiliş)","#16a085","Çekiliş")

        if t3 and on_numara:
            with t3:
                tum=[]
                for row in ON_NUMARA_ARSIV: tum.extend(row["sayilar"])
                freq=Counter(tum)
                st.caption(f"Arşivdeki {len(ON_NUMARA_ARSIV)} çekilişe göre frekans analizi")
                data=sorted(freq.items())
                goster_grafik(data,"Tüm Arşivde Çıkma Sayısı",renk,"Çıkma")

        if bonus and b_sicak:
            st.divider()
            st.markdown("**🌟 Şans Topu İstatistikleri**")
            bc1,bc2=st.columns(2)
            with bc1:
                st.caption("En çok çıkan şans topları")
                goster_top_listesi(b_sicak,bonus_renk,"×",n=7)
            with bc2:
                st.caption("En uzun çıkmayan şans topları")
                goster_top_listesi(b_soguk,"#888"," çekiliş",n=7)

    if st.button("🔄 Veriyi Yenile",key=f"yenile_{slug}"):
        st.cache_data.clear(); st.rerun()

# ─── Ana sayfa ────────────────────────────────────────────────────────────────
st.title("🍀 Loto Kombinasyon Üretici")
st.caption(f"Sayısal Loto · Süper Loto · Şans Topu · On Numara  |  On Numara arşivi: {len(ON_NUMARA_ARSIV)} çekiliş ({ON_NUMARA_ARSIV[-1]['tarih']} – {ON_NUMARA_ARSIV[0]['tarih']})")

tab1,tab2,tab3,tab4=st.tabs(list(OYUNLAR.keys()))
for tab,(isim,cfg) in zip([tab1,tab2,tab3,tab4],OYUNLAR.items()):
    with tab:
        oyun_sekmesi(cfg)

st.divider()
st.caption(f"Son yükleme: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
