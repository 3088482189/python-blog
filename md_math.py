import mistune
import re    
class MathLexer(mistune.InlineLexer):
    def __init__(self,*args,**kwargs):
        super(MathLexer,self).__init__(*args,**kwargs)
        self.rules.block_math=re.compile(r'\$\$([\s\S]+?)\$\$(?!\])')
        self.rules.inline_math=re.compile(r'^\$((?:\\\$|[^$])+?)\$')
        self.rules.text=re.compile(r'^[\s\S]+?(?=[\\<!\[_*`~\$]|https?://| {2,}\n|$)')
        self.default_rules.insert(0,'block_math')
        self.default_rules.insert(0,'inline_math')

    def output_inline_math(self,m):
        return self.renderer.inline_math(m.group(1))
    def output_block_math(self,m):
        return self.renderer.block_math(m.group(1))

class MathRenderer(mistune.Renderer):
    def block_math(self,text):
        return '<code><latex_display>%s</latex_display></code>'%text.replace('<','&lt;')
    def inline_math(self,text):
        return '<code><latex>%s</latex></code>'%text.replace('<','&lt;')

renderer=MathRenderer()
mathLexer=MathLexer(renderer)
parse=mistune.Markdown(renderer=renderer,inline=mathLexer)