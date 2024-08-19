import os
import argparse
from weasyprint import HTML
import pandas as pd

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Print table tags.")
    parser.add_argument("input", type=str)
    args = parser.parse_args()
    
    df = pd.read_excel(args.input)
    table_ids = df["Table ID"].unique()
    for tid in sorted(table_ids):
        pdf_filepath = os.path.join(f"table_{tid:02d}.pdf")
        idx = df["Table ID"] == tid
        demo_df = df[idx][["Name", "Primary Organization"]]
        table=demo_df.to_html(classes='mystyle', index=False)
        table = table.replace("dataframe", "dataframe center")
        html_string = f'''
        <html>
          <head><title>HTML Pandas Dataframe with CSS</title></head>
          <link rel="stylesheet" type="text/css" href="df_style.css"/>
          <body>
              <center>
            <h2> Table {tid:02d} </h2>
              </center>
            {table}
          </body>
        </html>
        '''
        
        HTML(string=html_string).write_pdf(pdf_filepath, stylesheets=["df_style.css"])
