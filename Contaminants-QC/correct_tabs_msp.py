import click

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
INFO = '''
The selected mgf file has {n} lines, of which {m} were corrected. 
'''

# def fix_mgf_title(line:str):
# 	return "TITLE=" + line.split('=')[-1]

# with open(mgf_output.name,'w') as f_o:
# 	with open(mgf_input, 'r') as f_i:
# 		for line in f_i:
# 			if line.startswith("TITLE"):
# 				f_o.write(fix_mgf_title(line))
# 			else:
# 				f_o.write(line)


def print_help():
    """
    Print the help of the tool
    :return:
    """
    ctx = click.get_current_context()
    click.echo(ctx.get_help())
    ctx.exit()

@click.command(short_help='correct_mgf_tabs will correct the peak data tab separation in any spectra of the mgf')
@click.argument('input_filepath', type=click.Path(exists=True,readable=True) )  # help="The input file path for the mgf to be corrected")
@click.argument('output_filepath', type=click.Path(writable=True) )  # help="The output destination path for the corrected mgf file")
def correct_mgf_tabs(input_filepath, output_filepath):
    """
    correct_mgf_tabs will correct only the peak data lines' tab separation if 
    any elments are separated by a blank rather than a tab for all lines.
    """
    if not any([input_filepath,output_filepath]):
        print_help()
    try:
        with open(input_filepath,'r') as infile:
            lines = infile.readlines()
    except Exception as e:
        click.echo(e)
        print_help()

    n=len(lines)
    corrected = [line.replace(' ','\t').strip()+'\t""' if line[0].isdigit() else line for line in lines]
    diff = sum([i!=j for i, j in zip(lines, corrected)])
    
    with open(output_filepath,'w') as file:
        file.writelines(corrected)
    
    print(INFO.format(m=diff, n=n))

if __name__ == '__main__':
    correct_mgf_tabs()