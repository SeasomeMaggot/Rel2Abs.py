import hou
import re

nodes = hou.selectedNodes()
if not nodes:
    hou.ui.displayMessage(
        "请先选中需要修改的节点。",
        severity=hou.severityType.Warning,
    )
else:
    # 匹配 ch, chs, chf, chi, chramp, chp, chraw, chsraw, chsop
    pattern = r'\b(ch(?:s(?:op|raw)?|f|i|ramp|p|raw)?)\s*\(\s*("|\')([^"\']*?)\2((?:\s*,[^)]*)?)\s*\)'
    modified = 0

    for node in nodes:
        for parm in node.parms():
            # 安全获取表达式，不支持则跳过
            try:
                expr = parm.expression()
            except hou.OperationFailed:
                continue
            if not expr:
                continue
            lang = parm.expressionLanguage()

            def replacer(m):
                func = m.group(1)
                quote = m.group(2)
                path_str = m.group(3)
                rest = m.group(4)

                if path_str.startswith('/'):
                    new_path = path_str
                else:
                    # 分离相对节点路径和参数名
                    if '/' in path_str:
                        last_slash = path_str.rfind('/')
                        node_rel = path_str[:last_slash]
                        parm_name = path_str[last_slash+1:]
                    else:
                        node_rel = '.'
                        parm_name = path_str

                    try:
                        resolved_node = node.node(node_rel)
                    except hou.OperationFailed:
                        resolved_node = None

                    if resolved_node is None:
                        new_path = path_str
                    else:
                        new_path = resolved_node.path() + '/' + parm_name

                return f'{func}({quote}{new_path}{quote}{rest})'

            new_expr = re.sub(pattern, replacer, expr)

            if new_expr != expr:
                try:
                    parm.setExpression(new_expr, lang)
                    modified += 1
                except Exception as e:
                    print(f"设置失败 {node.path()} / {parm.name()}: {e}")

    if modified:
        hou.ui.displayMessage(f"已修改 {modified} 个参数表达式。")
    else:
        hou.ui.displayMessage("没有需要修改的相对引用。", severity=hou.severityType.Important)
