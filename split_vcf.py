import argparse
import pandas as pd

def meta_info(file):
    with open(file, 'r') as combined:
        meta = ''
        meta_num = 0
        for line in combined:
            if line[1] == '#':
                meta += line
                meta_num += 1
        return meta, meta_num

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', dest='file', help='Name of the VCF file to split', type=str, required=True)
    args = parser.parse_args()

    meta, meta_num = meta_info(args.file)

    df = pd.read_csv(args.file, skiprows=meta_num, sep='\t', header=0)
    base = df[df.columns[0:9]]
    samples = df[df.columns[9:]]

    for column in samples:
        file = 'samples/' + column + '.vcf'
        new = base.copy()
        new[column] = samples[column]
        with open(file, 'w') as out:
            out.write(meta)
            out.write(new.to_csv(sep='\t', index=False))