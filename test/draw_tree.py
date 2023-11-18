from pyecharts import options as opts
from pyecharts.charts import Tree


data = [
    {
        "children": [
            {"children": [{"name": "I", "value": "0xffffff"}], "name": "E"}, 
            {"name": "F", "value": "0xffffff"}
        ],
        "name": "A",
        "value": "0xffffff"
    }
]
c = (
    Tree()
    .add("", data, orient="TB")
    .set_global_opts(title_opts=opts.TitleOpts(title="Tree-基本示例"))
    .render("./Test/tree_base.html")
)

