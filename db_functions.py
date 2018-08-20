import sqlite3
import pandas as pd


if __name__=='__main__':
    con = sqlite3.connect('db/pharmGKB_ann.sqlite')
    fn = r'annotations/clinical_ann.tsv'
    df = pd.read_csv(fn, sep='\t', header=0)
    #df = df[df.Location.str.contains("rs") == True]
    df.to_sql('clinical_ann', con, index=False)