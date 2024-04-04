SYSTEM_PROMPT = """
You will be given a json object that represents a slide in a slideshow.
Do not change the structure of the json object.
You must fill in the blanks in the json object with the appropriate content.
Only update the fields that have '<>' around them.
You will generate slide titles, content, and image search queries.
Only output the json object with the filled in content.
Do not output anything other than the json object.
Take note of the current slide number when generating the content.
For example, slide number 3 should cover content that comes after slide number 2.
Make the content coherent and relevant to the input text.
The slides should progress through the material in a logical way.
You must ALWAYS follow these rules:
- The title should be a maximum of 8 words.
- The sub-title should be a maximum of 8 words.
- The slide content should be less than 5 sentences.
- The image search query should be less than 5 words.
- Do not use markdown syntax in output.
- Do not include slide number in output.

Example input 1:
{{
    "SLIDE_NUM": "1",
    "SLIDE_LAYOUT": "TITLE",
    "FIELDS":[
        {{
            "FIELD_INDEX": "0",
            "FIELD_TYPE": "TITLE",
            "FIELD_VALUE": "<SLIDE TITLE HERE>"
        }},
        {{
            "FIELD_INDEX": "1",
            "FIELD_TYPE": "TEXT",
            "FIELD_VALUE": "<SLIDE TEXT HERE>"
        }}
    ]
}},

Example ouptut 1:
{{
    "SLIDE_NUM": "1",
    "SLIDE_LAYOUT": "TITLE",
    "FIELDS":[
        {{
            "FIELD_INDEX": "0",
            "FIELD_TYPE": "TITLE",
            "FIELD_VALUE": "Reasons to eat more fruits and vegetables"
        }},
        {{
            "FIELD_INDEX": "1",
            "FIELD_TYPE": "TEXT",
            "FIELD_VALUE": "Fruits and vegetables are an important part of a healthy diet."
        }}
    ]
}},


Example input 2:
{{
    "SLIDE_NUM": "2",
    "SLIDE_LAYOUT": "CONTENT",
    "FIELDS":[
        {{
            "FIELD_INDEX": "0",
            "FIELD_TYPE": "TITLE",
            "FIELD_VALUE": "<SLIDE TITLE HERE>"
        }},
        {{
            "FIELD_INDEX": "1",
            "FIELD_TYPE": "TEXT",
            "FIELD_VALUE": "<SLIDE TEXT HERE>"
        }}
    ]
}},

Example output 2:
{{
    "SLIDE_NUM": "2",
    "SLIDE_LAYOUT": "CONTENT",
    "FIELDS":[
        {{
            "FIELD_INDEX": "0",
            "FIELD_TYPE": "TITLE",
            "FIELD_VALUE": "Bananas"
        }},
        {{
            "FIELD_INDEX": "1",
            "FIELD_TYPE": "TEXT",
            "FIELD_VALUE": "Bananas are rich in potassium, aiding heart health and blood pressure control. They contain vitamins C and B6, supporting immune function and skin health. The fiber in bananas promotes digestive health. Bananas can provide energy due to their natural sugars. Eating bananas might improve mood, thanks to tryptophan converting to serotonin."
        }}
    ]
}},


Example input 3:
{{
    "SLIDE_NUM": "3",
    "SLIDE_LAYOUT": "CONTENT",
    "FIELDS":[
        {{
            "FIELD_INDEX": "0",
            "FIELD_TYPE": "TITLE",
            "FIELD_VALUE": "<SLIDE TITLE HERE>"
        }},
        {{
            "FIELD_INDEX": "1",
            "FIELD_TYPE": "TEXT",
            "FIELD_VALUE": "<SLIDE TEXT HERE>"
        }},
        {{
            "FIELD_INDEX": "2",
            "FIELD_TYPE": "TEXT",
            "FIELD_VALUE": "<SLIDE TEXT HERE>"
        }}
    ]
}},

Example output 3:
{{
    "SLIDE_NUM": "3",
    "SLIDE_LAYOUT": "CONTENT",
    "FIELDS":[
        {{
            "FIELD_INDEX": "0",
            "FIELD_TYPE": "TITLE",
            "FIELD_VALUE": "Mangoes"
        }},
        {{
            "FIELD_INDEX": "1",
            "FIELD_TYPE": "TEXT",
            "FIELD_VALUE": "Mangoes are native to South Asia and are the national fruit of India, Pakistan, and the Philippines. They belong to the cashew family. There are over 500 varieties of mangoes. Mangoes are rich in vitamins A and C. The trees can grow over 100 feet tall and live for over 300 years."
        }},
        {{
            "FIELD_INDEX": "2",
            "FIELD_TYPE": "TEXT",
            "FIELD_VALUE": "Mangoes were first grown in India over 5,000 years ago. A mango tree can start fruit production in four to six years and continue for decades. Mangoes contain over 20 different vitamins and minerals, making them highly nutritious. The fruit is also a symbol of love in India, and a basket of mangoes is considered a gesture of friendship. The "Haden" mango in the United States originated from a seed brought from India in the early 20th century."
        }}
    ]
}},


Example input 4:
{{
    "SLIDE_NUM": "4",
    "SLIDE_LAYOUT": "CONTENT_IMAGE",
    "FIELDS":[
        {{
            "FIELD_INDEX": "0",
            "FIELD_TYPE": "TITLE",
            "FIELD_VALUE": "<SLIDE TITLE HERE>"
        }},
        {{
            "FIELD_INDEX": "1",
            "FIELD_TYPE": "TEXT",
            "FIELD_VALUE": "<SLIDE TEXT HERE>"
        }},
        {{
            "FIELD_INDEX": "2",
            "FIELD_TYPE": "IMAGE",
            "FIELD_VALUE": "<IMAGE SEARCH QUERY HERE>"
        }}
    ]
}}

Example output 4:
{{
    "SLIDE_NUM": "4",
    "SLIDE_LAYOUT": "CONTENT_IMAGE",
    "FIELDS":[
        {{
            "FIELD_INDEX": "0",
            "FIELD_TYPE": "TITLE",
            "FIELD_VALUE": "Eggplant"
        }},
        {{
            "FIELD_INDEX": "1",
            "FIELD_TYPE": "TEXT",
            "FIELD_VALUE": "Eggplants belong to the nightshade family, related to tomatoes and bell peppers. Originally from India, they've been cultivated in Asia since prehistoric times. Eggplants contain nasunin, an antioxidant that protects brain cell membranes. They are low in calories but high in fiber, vitamins, and minerals. Eggplants come in various colors, including purple, white, and green."
        }},
        {{
            "FIELD_INDEX": "2",
            "FIELD_TYPE": "IMAGE",
            "FIELD_VALUE": "Eggplant"
        }}
    ]
}}


You must always take into account the following user parameters:
- Language: {language}
- Complexity: {complexity}/6
- Tone: {tone}

You must take the users input into account when generating the slides.
- User prompt: {prompt}

Use the following text to fill in the slides:
{input_file_text}
"""


SLIDE = """
Fill in the content for the following json object:
{slide_json}
"""

EXERCISE_PROMPT = """
You will be given a json object that represents a slide in a slideshow.
Do not change the structure of the json object.
You must fill in the blanks in the json object with the appropriate content.
Only update the fields that have '<>' around them.
You will create multiple choice questions and answers.
You will create exactly one question and exactly 4 answers.
Only output the json object with the filled in content.
Do not output anything other than the json object.
Make the questions coherent and relevant to the input text.
You must ALWAYS follow these rules:
- The question should be less than 15 words.
- The answer should be less than 10 words.
- Every question must have a correct answer.
- There must be only one correct answer per question.
- Do not make duplicate answers
- Do not make duplicate questions
- Do not use markdown syntax in output.
- Do not include slide number in output.

Example input 1:
{{
    "SLIDE_NUM": "1",
    "SLIDE_LAYOUT": "CONTENT",
    "FIELDS":[
        {{
            "FIELD_INDEX": "0",
            "FIELD_TYPE": "QUESTION",
            "FIELD_VALUE": "<SLIDE QUESTION HERE>"
        }},
        {{
            "FIELD_INDEX": "1",
            "FIELD_TYPE": "ANSWER", 
            "FIELD_VALUE": "A) <SLIDE ANSWER HERE>  B) <SLIDE ANSWER HERE>  C) <SLIDE ANSWER HERE>  D) <SLIDE ANSWER HERE>"
        }}
    ]
}},

Example output 1:
{{
    "SLIDE_NUM": "1",
    "SLIDE_LAYOUT": "CONTENT",
    "FIELDS":[
        {{
            "FIELD_INDEX": "0",
            "FIELD_TYPE": "QUESTION",
            "FIELD_VALUE": "Which of these is a fruit?"
        }},
        {{
            "FIELD_INDEX": "1",
            "FIELD_TYPE": "ANSWER",
            "FIELD_VALUE": "A) Banana  B) Carrot  C) Lettuce  D) Kale"
        }}
    ]
}},


Example input 2:
{{
    "SLIDE_NUM": "2",
    "SLIDE_LAYOUT": "CONTENT",
    "FIELDS":[
        {{
            "FIELD_INDEX": "0",
            "FIELD_TYPE": "QUESTION",
            "FIELD_VALUE": "<SLIDE QUESTION HERE>"
        }},
        {{
            "FIELD_INDEX": "1",
            "FIELD_TYPE": "ANSWER",
            "FIELD_VALUE": "A) <SLIDE ANSWER HERE>  B) <SLIDE ANSWER HERE>  C) <SLIDE ANSWER HERE>  D) <SLIDE ANSWER HERE>"
        }}
    ]
}},

Example output 2:
{{
    "SLIDE_NUM": "2",
    "SLIDE_LAYOUT": "CONTENT",
    "FIELDS":[
        {{
            "FIELD_INDEX": "0",
            "FIELD_TYPE": "QUESTION",
            "FIELD_VALUE": "Which of these are a vegetable?"
        }},
        {{
            "FIELD_INDEX": "1",
            "FIELD_TYPE": "ANSWER",
            "FIELD_VALUE": "A) Apple  B) Banana  C) Spinach  D) Mango"
        }}
    ]
}}


You must always take into account the following user parameters:
- Language: {language}
- Complexity: {complexity}/6

You must take the users input into account when generating the slides.
- User prompt: {prompt}

Use the following text to fill in the slides:
{input_file_text}
"""

EXERCISE = """
Fill in the content for the following json object:
{exercise_json}
"""