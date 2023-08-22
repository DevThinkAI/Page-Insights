import logging
import os
from pathlib import Path
from typing import Any
import gradio as gr

import dotenv
from page_insights.llm_adapter import LlmAdapter
from page_insights.prompts_manager import PromptsManager
from page_insights.summarizer import Summarizer
from page_insights.research_manager import ResearchManager

logging.basicConfig(level=logging.INFO)
dotenv.load_dotenv()

##################################################################################
# 
# [BUG-00] @TODO We are resetting the links list after save of the research (CheckBox group)
# But, If you gen yet another research, links from the previous research are still 
# there, being sent to the summarizer)  The old links add to any new links.      
#
##################################################################################


with gr.Blocks(title="Page insights") as demo:

    openai_key: str = os.getenv("OPENAI_API_KEY") # type: ignore
    assets_dir: Path = Path(os.getenv("ASSETS_FOLDER_PATH")) # type: ignore

    prompts_manager = PromptsManager(assets_dir)
    llm_adapter = LlmAdapter(openai_key, resp_max_tokens=1024)
    research_manager = ResearchManager(assets_dir)
    summarizer = Summarizer(prompts_manager, llm_adapter)


    def update_prompt(prompt_name: str, value: str) -> None:
        gr.Info("Prompt updated")
        prompts_manager.update_prompt(prompt_name, value)


    def load_prompt(prompt_name: str) -> str:
        return prompts_manager.get_prompt(prompt_name)
    
    def save_new_prompt(prompt_name: str, prompt_text: str) -> tuple[dict[str, Any], dict[str, Any]]:
        prompts_manager.add_prompt(prompt_name, prompt_text)
        gr.Info("New prompt saved")
        return gr.Dropdown.update(choices=prompts_manager.get_prompt_names(), value=prompt_name), \
            gr.Dropdown.update(choices=prompts_manager.get_prompt_names())
    

    def save_page_analysis(research_text: str, research_name: str, link: str) -> tuple[dict[str, Any],dict[str, Any],dict[str, Any],dict[str, Any],dict[str, Any]]:
        if not research_name.strip():
            raise gr.Error("Research name cannot be empty")
        try:
            research_manager.persist_research(research_text, research_name, [link])
            gr.Info("Research saved.  You can view it on the View Research tab")
        except Exception as e:
            raise gr.Error(str(e))
        # returns to blank out forms and update the research list on View Research tab
        return gr.Dropdown.update(choices=research_manager.get_research_ids()), \
            gr.Textbox.update(value=""), \
            gr.TextArea.update(value=""), \
            gr.Markdown.update(value=""), \
            gr.Textbox.update(value="")


    def research_preview(research_markdown: str) -> tuple[dict[str, Any]]:
        # The gradio ML viewer required 2 newlines to rener a single newline
        research_markdown = research_markdown.replace("\n", "\n\n")
        return gr.TextArea.update(visible=False), gr.Markdown.update(visible=True, value=research_markdown) # type: ignore

    def research_edit() -> tuple[dict[str, Any]]:
        return gr.TextArea.update(visible=True), gr.Markdown.update(visible=False) # type: ignore
    
    def get_research_details(research_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        research_metadata, research_text  = research_manager.get_research_details(research_id)
        # The gradio ML viewer required 2 newlines to rener a single newline
        research_markdown_txt = research_text.replace("\n", "\n\n")
        return gr.JSON.update(value=research_metadata), gr.Markdown.update(value=research_markdown_txt)
    
    
    def get_page_analysis(link: str, temprature: float, prompt_select: str, output_max_range: str) -> tuple[str, str]:
        # raise error if link or prompt or output_max_range is empty
        if not link.strip() or not prompt_select.strip() or not output_max_range.strip():
            raise gr.Error("Link, prompt, and/or output_max_range cannot be empty")
        return summarizer.get_summary_for_url(link, temprature, prompt_select, output_max_range)
    
    def archive_research(research_id: str) -> tuple[dict[str,Any], dict[str,Any], dict[str,Any]]:
        research_manager.delete_research(research_id)
        gr.Info(f"Research {research_id} archived")
        return gr.Dropdown.update(choices=research_manager.get_research_ids(), value=None), \
            gr.JSON.update(value=None), \
            gr.Markdown.update(value="")


    gr.Markdown("# Page insights; a research assistant")

    ###############################################################
    # Page analysis
    with gr.Tab("Page analysis"):
        gr.Markdown("""## Apply a prompt instruction to the content of the link supplied
                1. Select a prompt (*prompts can be viewed/edited on the `[Manage Prompts]` tab*)
                2. Select a [temperature](https://learnprompting.org/docs/basics/configuration_hyperparameters#temperature)
                3. Input a wordcount range applied to each summary. This can be used in the prompt to control the length of the summary from the LLM
                3. Supply a link to be analyzed
                4. Click **Analyze**
                
                You will then be able to preview and edit (supports markdown) the generated research
                    
                Finally, click Save to persist the insight document.
                Saved insights documents can be found on the `[Page Insights]` tab""")
        page_analyze_prompt_select = gr.Dropdown(
            choices=prompts_manager.get_prompt_names(),
            label="Prompt",
            type="value",
        )
        page_analysis_link = gr.Textbox(label="URL", placeholder="https://example.com")
        temp_input = gr.Slider(0.0, 2.0, label="LLM Temperature", step=0.1, value=0.0)
        output_max_range = gr.Text(label="LLM output min,max range", value="150, 200", lines=1)
        analysys_btn = gr.Button("Analyze")
        page_analysis_output_md = gr.Textbox(label="Output", lines=10, show_copy_button=True)
        page_analysis_output_rendered = gr.Markdown(label="Output", visible=False)
        with gr.Row():
            page_analysis_view_md_btn = gr.Button("View markdown")
            page_analysis_view_rendered_btn = gr.Button("View rendered")
        with gr.Accordion("Debug output", open=False):
            txt_debug = gr.Textbox(label="Output", lines=10)
        with gr.Row():
            with gr.Column(scale=2):
                page_analyze_name = gr.Textbox(label="Name", lines=1)
            with gr.Column(scale=1):
                page_analyze_save_btn = gr.Button("Save")
        
    ###############################################################
    # View research tab

    with gr.Tab("Page insights"):
        gr.Markdown("""## View saved page insights   
                    Select an insight and view its metadata and content
                    """)
        view_research_list = gr.Dropdown(
            choices=research_manager.get_research_ids(),
            label="Select page insight",
            type="value",
        )
        view_research_details = gr.JSON(label="Page insight details")
        gr.Markdown("View a the plain text markdown or rendered")
        with gr.Row():
                view_research_edit_btn = gr.Button("Markdown")
                view_research_preview_btn = gr.Button("Rendered")
        view_research_md = gr.TextArea(label="Markdown", lines=30, show_copy_button=True, interactive=False)
        view_research_rendered = gr.Markdown(label="Rendered", visible=False)
        gr.Markdown("Archive this research doc")
        view_research_archive_btn = gr.Button("Archive")

    ###############################################################
    # Manage prompts
    with gr.Tab("Manage prompts"):
        gr.Markdown("""## Manage your prompts   
                    You can have as many prompts as you want.  This tab allows you to edit and create new prompts.

                    Available placeholders are `{{min_llm_resp_word_count}}` and `{{max_llm_resp_word_count}}`

                    `{{web_page_content}}` is the content of the webpage you are summarizing, this is **Required**

                    To create a new prompt, select and exiting prompt, then supplay a new name and click Save As New
                    """)
        prompt_select = gr.Dropdown(
            choices=prompts_manager.get_prompt_names(),
            label="Prompt",
            type="value",
        )
        prompt_edit_input = gr.Textbox(label="Prompt", lines=20, show_copy_button=True)
        update_prompt_button = gr.Button("Update")
        with gr.Row():
            with gr.Column():
                prompt_name = gr.Textbox(label="New prompt name", lines=1)
            with gr.Column():
                save_new_prompt_button = gr.Button("Save as new")


            

    ###############################################################
    # Listeners

    analysys_btn.click(
        get_page_analysis,
        inputs=[page_analysis_link, temp_input, page_analyze_prompt_select, output_max_range],
        outputs=[page_analysis_output_md, txt_debug],
    )
    
    # Promts management
    save_new_prompt_button.click(save_new_prompt, inputs=[prompt_name, prompt_edit_input], 
                                 outputs=[prompt_select, page_analyze_prompt_select])
    update_prompt_button.click(update_prompt, inputs=[prompt_select, prompt_edit_input])
    prompt_select.select(load_prompt, inputs=[prompt_select], outputs=[prompt_edit_input])

    # Reseach Viewer
    view_research_preview_btn.click(research_preview, inputs=[view_research_md], outputs=[view_research_md, view_research_rendered])
    view_research_edit_btn.click(research_edit, inputs=None, outputs=[view_research_md, view_research_rendered])
    view_research_list.select(get_research_details, inputs=[view_research_list], outputs=[view_research_details, view_research_md])
    view_research_archive_btn.click(archive_research, inputs=[view_research_list], outputs=[view_research_list,view_research_details,view_research_rendered])

    # Page Analysis
    page_analysis_view_rendered_btn.click(research_preview, inputs=[page_analysis_output_md], outputs=[page_analysis_output_md, page_analysis_output_rendered])
    page_analysis_view_md_btn.click(research_edit, inputs=None, outputs=[page_analysis_output_md, page_analysis_output_rendered])
    page_analyze_save_btn.click(save_page_analysis, 
                                inputs=[page_analysis_output_md, page_analyze_name, page_analysis_link],
                                outputs=[view_research_list, page_analysis_link, page_analysis_output_md, page_analysis_output_rendered, page_analyze_name])


    # handle browser refreshes
    # demo.load()


demo.queue().launch(debug=True) # YOu need queue in order for UI info/warn messages to show

