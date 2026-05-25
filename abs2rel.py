import hou
import re

nodes = hou.selectedNodes()
if not nodes:
    hou.ui.displayMessage(
        "请先选中需要修改的节点。",
        severity=hou.severityType.Warning,
    )
else:
    # 匹配 ch / chs / chf / chi / chramp / chp / chsraw / chraw / chsop
    pattern = r'\b(ch(?:s(?:op|raw)?|f|i|ramp|p|raw)?)\s*\(\s*("|\')([^"\']*?)\2((?:\s*,[^)]*)?)\s*\)'
    modified = 0

    for node in nodes:
        for parm in node.parms():
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

                # 只处理绝对路径
                if not path_str.startswith('/'):
                    return m.group(0)  # 保持原样

                # 分离节点路径和参数名（最后一个 '/' 之后为参数名）
                last_slash = path_str.rfind('/')
                if last_slash == -1:
                    # 理论上不会出现，因为以 '/' 开头至少有一个 '/'
                    return m.group(0)

                node_abs_path = path_str[:last_slash]
                parm_name = path_str[last_slash + 1:]

                # 尝试获取目标节点
                try:
                    target_node = hou.node(node_abs_path)
                except hou.OperationFailed:
                    target_node = None

                if target_node is None:
                    return m.group(0)  # 无法解析，保持原样

                # 计算相对路径
                rel_path = node.relativePathTo(target_node)
                new_path = rel_path + '/' + parm_name

                return f'{func}({quote}{new_path}{quote}{rest})'

            new_expr = re.sub(pattern, replacer, expr)

            if new_expr != expr:
                try:
                    parm.setExpression(new_expr, lang)
                    modified += 1
                except Exception as e:
                    print(f"设置失败 {node.path()} / {parm.name()}: {e}")

    if modified:
        hou.ui.displayMessage(f"已转换 {modified} 个绝对引用为相对引用。")
    else:
        hou.ui.displayMessage("没有需要转换的绝对引用。", severity=hou.severityType.Important)
