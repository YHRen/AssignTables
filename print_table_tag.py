import os
import argparse
from weasyprint import HTML
import pandas as pd

def parse_txt(filename):
    names, orgs, tables, tid = [], [], [], 0
    with open(filename, "r") as fp:
        for line in fp:
            if line.startswith("-----"):
                tid += 1
            if "years" in line:
                print(line)
                tokens = line.split()
                idx = tokens.index("years")
                name, org = " ".join(tokens[1 : idx - 2]), tokens[idx - 2]
                names.append(name)
                orgs.append(org)
                tables.append(tid)
    return pd.DataFrame(data={"Name": names, "Primary Organization": orgs, "Table ID": tables})


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Print table tags.")
    parser.add_argument("input", type=str)
    args = parser.parse_args()
    
    if args.input.endswith("xlsx"):
        df = pd.read_excel(args.input)
    elif args.input.endswith("txt"):
        df = parse_txt(args.input)

    table_ids = df["Table ID"].unique()
    for tid in sorted(table_ids):
        pdf_filepath = os.path.join(f"table_{tid:02d}.pdf")
        idx = df["Table ID"] == tid
        demo_df = df[idx][["Name", "Primary Organization"]]
        table=demo_df.to_html(classes='mystyle', index=False, justify='left')
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
