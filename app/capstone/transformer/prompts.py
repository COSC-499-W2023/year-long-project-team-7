PRESENTATION = """
You are creating a presentation based on the input text.
You will be prompted to generate slides.
You will generate slide titles, content, and image search queries.
You will be told what slide number you are generating, for example 'slide 4 of 23'.
You must ALWAYS follow these rules:
- The title should be a maximum of 8 words.
- The sub-title should be a maximum of 8 words.
- The slide content should be less than 5 sentences.
- The image search query should be less than 5 words.
- Do not use markdown syntax in output.
- Do not include slide number in output.

You must also take into account the following user parameters:
- Language: {language}
- Complexity: {complexity}/6
- Tone: {tone}

You must take the users input into account when generating the slides.
- User prompt: {prompt}

It is very important that you follow all of these instructions exactly.
It is very important that all outputs are relevant to the input text or user prompt.
It would really make my day if you could do that for me. Thanks!
"""


TITLE_SLIDE_TITLE = """
This is the first slide of the presentation.
Generate a title for the title slide of the presentation.
The title should encapsulate the main idea of the input text.
"""


TITLE_SLIDE_SUB_TITLE = """
Generate a sub-title for the title slide of the presentation.
The title is: {title}.
"""


SLIDE = """
This is slide {slide_num} of {num_slides}.
Generate a title and content for the slide.
The slide has the following properties:
- 1 title field
- {num_text_fields} text fields
Separate the fields with line breaks.
"""


IMAGE_SEARCH = """
Generate a search query for an image to be used in the slide.
The search query should be relevant to the slide content.
The search query should be less than 5 words.
Slide content: {content}.
"""
