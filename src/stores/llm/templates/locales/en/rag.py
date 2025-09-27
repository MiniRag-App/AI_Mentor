from string import Template

#### Rag Prompts #####

### system ### 

from string import Template

system_prompt = Template("\n".join([
    "you are an assistant to generate a response for the user",
    "you will be provided by a set of documents associated with the user's query.",
    "you have to generate a response based on a document provided",
    "Ignore the documents that are not relevant to the user's query",
    "you can apologize to the user if are not able to generate a response",
    "you have to generate response with the same language of the user's query",
    "be polit and respectafull for the user",
    "Be precise and consise in your response . Avoid unnecessay information"
]))


### Document ###

Document_prompt =Template(
        "\n".join([
        "### Doncuemnt_NO: $doc_num",
        "## Content: $chunk_text "
    ]))


### Footer ###

Footer_prompt=Template(
    "\n".join([
        "Based on the above documents please generate the answer for the user",
        "##Question:",
        "$query",
        "",
        "## Answer: ",
    ])
)