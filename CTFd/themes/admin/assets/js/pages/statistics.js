import "./main";
import CTFd from "../compat/CTFd";
import $ from "jquery";
import echarts from "echarts/dist/echarts.common";
import { colorHash } from "../compat/styles";
import Vue from "vue";
import ScoreboardMatrix from "../components/statistics/ScoreboardMatrix.vue";

// 通用对齐表格构建：第一列左对齐，其余列居中，表格整体水平居中
// 用 HTML 表格而非文本 pad，避免等宽字体宽度计算误差导致的列错位
const buildAlignedTable = (headers, cols) => {
  const table = document.createElement("table");
  table.style.cssText =
    "margin:0 auto;border-collapse:collapse;font-family:Menlo,Consolas,monospace;font-size:13px;";

  const thead = document.createElement("thead");
  const trHead = document.createElement("tr");
  headers.forEach((h, i) => {
    const th = document.createElement("th");
    th.textContent = h;
    th.style.cssText =
      "padding:6px 24px;border-bottom:1px solid #ddd;" +
      (i === 0 ? "text-align:left;" : "text-align:center;");
    trHead.appendChild(th);
  });
  thead.appendChild(trHead);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  const rowCount = cols[0].length;
  for (let r = 0; r < rowCount; r++) {
    const tr = document.createElement("tr");
    cols.forEach((col, ci) => {
      const td = document.createElement("td");
      td.textContent = col[r] == null ? "" : String(col[r]);
      td.style.cssText =
        "padding:6px 24px;" + (ci === 0 ? "text-align:left;" : "text-align:center;");
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);

  // 外层容器水平居中表格，并保留一定内边距
  const wrapper = document.createElement("div");
  wrapper.style.cssText = "padding:10px 20px;text-align:center;";
  wrapper.appendChild(table);
  return wrapper;
};

// 柱状图数据视图：生成对齐的只读 HTML 表格
// 兼容 xAxis.category（纵向柱）与 yAxis.category（横向柱）两种轴向
const barDataViewOptionToContent = (opt) => {
  const xAxis = opt.xAxis || [];
  const yAxis = opt.yAxis || [];
  const series = opt.series || [];

  // 找到 category 轴的数据（题目名/分段名）
  let categories = [];
  const xIsCategory =
    Array.isArray(xAxis) &&
    xAxis.length > 0 &&
    xAxis[0].type === "category" &&
    Array.isArray(xAxis[0].data);
  const yIsCategory =
    !xIsCategory &&
    Array.isArray(yAxis) &&
    yAxis.length > 0 &&
    yAxis[0].type === "category" &&
    Array.isArray(yAxis[0].data);

  if (xIsCategory) {
    categories = xAxis[0].data.slice();
  } else if (yIsCategory) {
    categories = yAxis[0].data.slice();
  }

  // 第一列表头用 _("Challenge Name") 走 i18n（中文→“题目名称”，英文→“Challenge Name”）
  const headers = [_("Challenge Name")].concat(series.map((s) => s.name || " "));
  // 每个 series 的数据：横向柱时 data 顺序与 categories 一致；纵向柱时也一致
  const cols = [categories];
  series.forEach((s) => {
    const arr = (s.data || []).map((d) => {
      if (d == null) return "";
      if (typeof d === "object") {
        return d.value == null ? "" : String(d.value);
      }
      return String(d);
    });
    cols.push(arr);
  });

  return buildAlignedTable(headers, cols);
};

// 环形图（pie）数据视图：生成对齐的只读 HTML 表格
// pie 的 series.data 是 [{name, value, ...}] 数组，取 name 作为第一列，value 作为第二列
const pieDataViewOptionToContent = (opt) => {
  const series = opt.series || [];
  // 取第一个 pie series 的数据（statistics 页环形图均只有一个 series）
  const s = series[0] || {};
  const data = Array.isArray(s.data) ? s.data : [];

  // 第一列用 _("Name") 走 i18n（中文→“名称”，英文→“Name”），第二列用 series.name 作为表头
  const headers = [_("Name"), s.name || "数值"];
  const names = [];
  const values = [];
  data.forEach((d) => {
    if (d == null) return;
    if (typeof d === "object") {
      names.push(d.name == null ? "" : String(d.name));
      values.push(d.value == null ? "" : String(d.value));
    } else {
      names.push("");
      values.push(String(d));
    }
  });

  return buildAlignedTable(headers, [names, values]);
};

const graph_configs = {
  "#solves-graph": {
    data: () => CTFd.api.get_challenge_solve_statistics(),
    format: (response) => {
      const data = response.data;
      const chals = [];
      const counts = [];
      const solves = {};
      for (let c = 0; c < data.length; c++) {
        solves[data[c]["id"]] = {
          name: data[c]["name"],
          solves: data[c]["solves"],
        };
      }

      const solves_order = Object.keys(solves).sort(function (a, b) {
        return solves[b].solves - solves[a].solves;
      });

      $.each(solves_order, function (key, value) {
        chals.push(solves[value].name);
        counts.push(solves[value].solves);
      });

      const option = {
        title: {
          left: "center",
          text: _("Solve Counts"),
        },
        tooltip: {
          trigger: "item",
        },
        toolbox: {
          show: true,
          feature: {
            mark: { show: true },
            dataView: {
              show: true,
              readOnly: true,
              optionToContent: barDataViewOptionToContent,
              lang: [_("Data View"), _("Close"), _("Refresh")],
            },
            magicType: { show: true, type: ["line", "bar"] },
            restore: { show: true },
            saveAsImage: { show: true },
          },
        },
        xAxis: {
        name: _("Solve Count"),
        nameGap: 40,
        nameLocation: "middle",
        type: "value",
      },
        yAxis: {
          name: _("Challenge Name"),
          nameLocation: "middle",
          nameGap: 60,
          type: "category",
          data: chals,
          axisLabel: {
            interval: 0,
            rotate: 0, //If the label names are too long you can manage this by rotating the label.
          },
        },
        dataZoom: [
          {
            show: false,
            start: 0,
            end: 100,
          },
          {
            type: "inside",
            yAxisIndex: 0,
            show: true,
            width: 20,
          },
          {
            fillerColor: "rgba(233, 236, 241, 0.4)",
            show: true,
            yAxisIndex: 0,
            width: 20,
          },
        ],
        series: [
          {
            name: _("Solve Counts"),
            itemStyle: { normal: { color: "#1f76b4" } },
            data: counts,
            type: "bar",
          },
        ],
      };

      return option;
    },
  },

  "#keys-pie-graph": {
    data: () => CTFd.api.get_submission_property_counts({ column: "type" }),
    format: (response) => {
      const data = response.data;
      const solves = data["correct"] || 0;
      const fails = data["incorrect"] || 0;

      // 没有任何提交时使用空数据，显示灰色占位环形图（参考分类细分/积分细分图表）
      const hasSubmissions = solves > 0 || fails > 0;

      let pieData;
      let legendData;
      if (hasSubmissions) {
        pieData = [
          {
            value: fails,
            name: _("Fails"),
            itemStyle: { color: "rgb(207, 38, 0)" },
          },
          {
            value: solves,
            name: _("Solves"),
            itemStyle: { color: "rgb(0, 209, 64)" },
          },
        ];
        legendData = [_("Fails"), _("Solves")];
      } else {
        pieData = [];
        legendData = [];
      }

      let option = {
        title: {
          left: "center",
          text: _("Submission Percentages"),
        },
        tooltip: {
          trigger: "item",
        },
        toolbox: {
          show: true,
          feature: {
            dataView: {
              show: true,
              readOnly: true,
              optionToContent: pieDataViewOptionToContent,
              lang: [_("Data View"), _("Close"), _("Refresh")],
            },
            saveAsImage: {},
          },
        },
        legend: {
          orient: "vertical",
          top: "middle",
          right: 0,
          data: legendData,
        },
        series: [
          {
            name: _("Submission Percentages"),
            type: "pie",
            radius: ["30%", "50%"],
            avoidLabelOverlap: false,
            label: {
              show: false,
              position: "center",
            },
            itemStyle: {
              normal: {
                label: {
                  show: true,
                  formatter: function (data) {
                    return `${data.name} (${data.value})\n${data.percent.toFixed(1)}%`;
                  },
                },
                labelLine: {
                  show: true,
                },
              },
              emphasis: {
                label: {
                  show: true,
                  position: "center",
                  textStyle: {
                    fontSize: "14",
                    fontWeight: "normal",
                  },
                },
              },
            },
            emphasis: {
              label: {
                show: true,
                fontSize: "30",
                fontWeight: "bold",
              },
            },
            labelLine: {
              show: false,
            },
            data: pieData,
          },
        ],
      };

      return option;
    },
  },

  "#categories-pie-graph": {
    data: () => CTFd.api.get_challenge_property_counts({ column: "category" }),
    format: (response) => {
      const data = response.data;

      const categories = [];
      const count = [];

      for (let category in data) {
        if (Object.hasOwn(data, category)) {
          categories.push(category);
          count.push(data[category]);
        }
      }

      for (let i = 0; i < data.length; i++) {
        categories.push(data[i].category);
        count.push(data[i].count);
      }

      let option = {
        title: {
          left: "center",
          text: _("Category Breakdown"),
        },
        tooltip: {
          trigger: "item",
        },
        toolbox: {
          show: true,
          feature: {
            dataView: {
              show: true,
              readOnly: true,
              optionToContent: pieDataViewOptionToContent,
              lang: [_("Data View"), _("Close"), _("Refresh")],
            },
            saveAsImage: {},
          },
        },
        legend: {
          type: "plain",
          orient: "horizontal",
          top: "bottom",
          data: [],
        },
        series: [
          {
            name: _("Category Breakdown"),
            type: "pie",
            radius: ["30%", "50%"],
            label: {
              show: false,
              position: "center",
            },
            itemStyle: {
              normal: {
                label: {
                  show: true,
                  formatter: function (data) {
                    return `${data.name} (${data.value})\n${data.percent.toFixed(1)}%`;
                  },
                },
                labelLine: {
                  show: true,
                },
              },
              emphasis: {
                label: {
                  show: true,
                  position: "center",
                  textStyle: {
                    fontSize: "14",
                    fontWeight: "normal",
                  },
                },
              },
            },
            emphasis: {
              label: {
                show: true,
                fontSize: "30",
                fontWeight: "bold",
              },
            },
            data: [],
          },
        ],
      };

      categories.forEach((category, index) => {
        option.legend.data.push(category);
        option.series[0].data.push({
          value: count[index],
          name: category,
          itemStyle: { color: colorHash(category) },
        });
      });

      return option;
    },
  },

  "#points-pie-graph": {
    data: () => {
      return CTFd.fetch(
        "/api/v1/statistics/challenges/category?function=sum&target=value",
        {
          method: "GET",
          credentials: "same-origin",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
        },
      ).then(function (response) {
        return response.json();
      });
    },
    format: (response) => {
      const data = response.data;

      const categories = [];
      const count = [];

      for (let category in data) {
        if (Object.hasOwn(data, category)) {
          categories.push(category);
          count.push(data[category]);
        }
      }

      for (let i = 0; i < data.length; i++) {
        categories.push(data[i].category);
        count.push(data[i].count);
      }

      let option = {
        title: {
          left: "center",
          text: _("Point Breakdown"),
        },
        tooltip: {
          trigger: "item",
        },
        toolbox: {
          show: true,
          feature: {
            dataView: {
              show: true,
              readOnly: true,
              optionToContent: pieDataViewOptionToContent,
              lang: [_("Data View"), _("Close"), _("Refresh")],
            },
            saveAsImage: {},
          },
        },
        legend: {
          type: "plain",
          orient: "horizontal",
          top: "bottom",
          data: [],
        },
        series: [
          {
            name: _("Point Breakdown"),
            type: "pie",
            radius: ["30%", "50%"],
            label: {
              show: false,
              position: "center",
            },
            itemStyle: {
              normal: {
                label: {
                  show: true,
                  formatter: function (data) {
                    return `${data.name} (${data.value})\n${data.percent.toFixed(1)}%`;
                  },
                },
                labelLine: {
                  show: true,
                },
              },
              emphasis: {
                label: {
                  show: true,
                  position: "center",
                  textStyle: {
                    fontSize: "14",
                    fontWeight: "normal",
                  },
                },
              },
            },
            emphasis: {
              label: {
                show: true,
                fontSize: "30",
                fontWeight: "bold",
              },
            },
            data: [],
          },
        ],
      };

      categories.forEach((category, index) => {
        option.legend.data.push(category);
        option.series[0].data.push({
          value: count[index],
          name: category,
          itemStyle: { color: colorHash(category) },
        });
      });

      return option;
    },
  },

  "#solve-percentages-graph": {
    layout: (annotations) => ({
      title: _("Solve Percentages per Challenge"),
      xaxis: {
        title: _("Challenge Name"),
      },
      yaxis: {
        title:
          _("Percentage of ") +
          CTFd.config.userMode.charAt(0).toUpperCase() +
          CTFd.config.userMode.slice(1) +
          _(" (%)"),
        range: [0, 100],
      },
      annotations: annotations,
    }),
    data: () => CTFd.api.get_challenge_solve_percentages(),
    format: (response) => {
      const data = response.data;

      const names = [];
      const percents = [];

      const annotations = [];

      for (let key in data) {
        names.push(data[key].name);
        percents.push(data[key].percentage * 100);

        const result = {
          x: data[key].name,
          y: data[key].percentage * 100,
          text: Math.round(data[key].percentage * 100) + "%",
          xanchor: "center",
          yanchor: "bottom",
          showarrow: false,
        };
        annotations.push(result);
      }

      const option = {
        title: {
          left: "center",
          text: _("Solve Percentages per Challenge"),
        },
        tooltip: {
          trigger: "item",
          formatter: function (data) {
            return `${echarts.format.encodeHTML(data.name)} - ${(
              Math.round(data.value * 10) / 10
            ).toFixed(1)}%`;
          },
        },
        toolbox: {
          show: true,
          feature: {
            mark: { show: true },
            dataView: {
              show: true,
              readOnly: true,
              optionToContent: barDataViewOptionToContent,
              lang: [_("Data View"), _("Close"), _("Refresh")],
            },
            magicType: { show: true, type: ["line", "bar"] },
            restore: { show: true },
            saveAsImage: { show: true },
          },
        },
        xAxis: {
          name: _("Challenge Name"),
          nameGap: 40,
          nameLocation: "middle",
          type: "category",
          data: names,
          axisLabel: {
            interval: 0,
            rotate: 50,
          },
        },
        yAxis: {
          name:
            _("Percentage of ") +
            CTFd.config.userMode.charAt(0).toUpperCase() +
            CTFd.config.userMode.slice(1) +
            _(" (%)"),
          nameGap: 50,
          nameLocation: "middle",
          type: "value",
          min: 0,
          max: 100,
        },
        dataZoom: [
          {
            show: false,
            start: 0,
            end: 100,
          },
          {
            type: "inside",
            show: true,
            start: 0,
            end: 100,
          },
          {
            fillerColor: "rgba(233, 236, 241, 0.4)",
            show: true,
            yAxisIndex: 0,
            width: 20,
          },
          {
            type: "slider",
            fillerColor: "rgba(233, 236, 241, 0.4)",
            top: 35,
            height: 20,
            show: true,
            start: 0,
            end: 100,
          },
        ],
        series: [
          {
            name: _("Solve Percentages per Challenge"),
            itemStyle: { normal: { color: "#1f76b4" } },
            data: percents,
            type: "bar",
          },
        ],
      };

      return option;
    },
  },

  "#score-distribution-graph": {
    layout: (annotations) => ({
      title: _("Score Distribution"),
      xaxis: {
        title: _("Score Bracket"),
        showticklabels: true,
        type: "category",
      },
      yaxis: {
        title:
          _("Number of ") +
          CTFd.config.userMode.charAt(0).toUpperCase() +
          CTFd.config.userMode.slice(1),
      },
      annotations: annotations,
    }),
    data: () =>
      CTFd.fetch("/api/v1/statistics/scores/distribution").then(
        function (response) {
          return response.json();
        },
      ),
    format: (response) => {
      const data = response.data.brackets;
      const keys = [];
      const brackets = [];
      const sizes = [];

      for (let key in data) {
        keys.push(parseInt(key));
      }
      keys.sort((a, b) => a - b);

      let start = "<0";
      keys.map((key) => {
        brackets.push(`${start} - ${key}`);
        sizes.push(data[key]);
        start = key;
      });

      const option = {
        title: {
          left: "center",
          text: _("Score Distribution"),
        },
        tooltip: {
          trigger: "item",
        },
        toolbox: {
          show: true,
          feature: {
            mark: { show: true },
            dataView: {
              show: true,
              readOnly: true,
              optionToContent: barDataViewOptionToContent,
              lang: [_("Data View"), _("Close"), _("Refresh")],
            },
            magicType: { show: true, type: ["line", "bar"] },
            restore: { show: true },
            saveAsImage: { show: true },
          },
        },
        xAxis: {
          name: _("Score Bracket"),
          nameGap: 40,
          nameLocation: "middle",
          type: "category",
          data: brackets,
        },
        yAxis: {
          name:
            _("Number of ") +
            CTFd.config.userMode.charAt(0).toUpperCase() +
            CTFd.config.userMode.slice(1),
          nameGap: 50,
          nameLocation: "middle",
          type: "value",
        },
        dataZoom: [
          {
            show: false,
            start: 0,
            end: 100,
          },
          {
            type: "inside",
            show: true,
            start: 0,
            end: 100,
          },
          {
            fillerColor: "rgba(233, 236, 241, 0.4)",
            show: true,
            yAxisIndex: 0,
            width: 20,
          },
          {
            type: "slider",
            fillerColor: "rgba(233, 236, 241, 0.4)",
            top: 35,
            height: 20,
            show: true,
            start: 0,
            end: 100,
          },
        ],
        series: [
          {
            name: _("Score Distribution"),
            itemStyle: { normal: { color: "#1f76b4" } },
            data: sizes,
            type: "bar",
          },
        ],
      };

      return option;
    },
  },
};

// 移动端下三个环形图的标题与环形图留白从 91px 改为 60px
// 通过设置 series.center 实现，仅在小屏幕（<=767.98px）生效，不影响桌面端
// 移动端下统一分类细分和积分细分的 Legend 上留白为 60px
const mobilePieKeys = [
  "#keys-pie-graph",
  "#categories-pie-graph",
  "#points-pie-graph",
];
const applyMobilePieCenter = (key, option) => {
  if (
    window.matchMedia("(max-width: 767.98px)").matches &&
    mobilePieKeys.indexOf(key) !== -1 &&
    option.series &&
    option.series[0]
  ) {
    option.series[0].center = ["50%", "42.06%"];
    if (option.legend) {
      if (key === "#categories-pie-graph") {
        option.legend.top = 305;
      } else if (key === "#points-pie-graph") {
        option.legend.top = 308;
      }
    }
  }
  return option;
};

// 移动端下图表标题过长会与右上角工具箱图标重叠
// 仅在小屏幕（<=767.98px）生效：测量标题文本宽度与工具箱占据宽度，
// 计算居中标题右边沿与工具箱左边沿的重叠量，若重叠则将标题左移该重叠量（参考 translateX(-overlap) 方案）
// 桌面端宽度充足，不做任何改动
const MOBILE_BP = "(max-width: 767.98px)";
// 需要应用移动端标题避让的图表（解题数 / 得分分布 / 各题目解题百分比）
const mobileTitleShiftKeys = [
  "#solves-graph",
  "#score-distribution-graph",
  "#solve-percentages-graph",
];

const countToolboxIcons = (feature) => {
  if (!feature) return 0;
  let n = 0;
  if (feature.mark && feature.mark.show) n++;
  if (feature.dataView && feature.dataView.show) n++;
  if (feature.magicType && feature.magicType.show) {
    n += (feature.magicType.type || []).length || 1;
  }
  if (feature.restore && feature.restore.show) n++;
  if (feature.saveAsImage && feature.saveAsImage.show) n++;
  return n;
};

const measureTitleTextWidth = (title) => {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  const ts = title.textStyle || {};
  const fontSize = ts.fontSize || 18;
  const fontWeight = ts.fontWeight || "normal";
  const fontFamily = ts.fontFamily || "sans-serif";
  ctx.font = fontWeight + " " + fontSize + "px " + fontFamily;
  return ctx.measureText(title.text).width;
};

// 计算 ECharts 工具箱在容器右侧占据的宽度（图标数 * itemSize + 间隙 + 右侧留白）
const estimateToolboxWidth = (toolbox) => {
  if (!toolbox || toolbox.show === false) return 0;
  const icons = countToolboxIcons(toolbox.feature);
  if (icons === 0) return 0;
  const itemSize = toolbox.itemSize || 15;
  const itemGap = toolbox.itemGap || 8;
  // 16px 覆盖工具箱自身右侧内边距，避免标题与图标贴得太近
  return icons * itemSize + (icons - 1) * itemGap + 16;
};

// 在 setOption 之后调用：若移动端标题与工具箱重叠，则左移标题（与参考代码 translateX(-overlap) 一致）
// 仅作用于 mobileTitleShiftKeys 中的图表，不影响其它图表与桌面端
const fixMobileTitleOverlap = (key, chart, option) => {
  if (mobileTitleShiftKeys.indexOf(key) === -1) return;
  if (!window.matchMedia(MOBILE_BP).matches) return;
  if (option.title == null || !option.title.text) return;
  const chartWidth = chart.getWidth();
  if (!chartWidth) return;

  const titleWidth = measureTitleTextWidth(option.title);
  const toolboxWidth = estimateToolboxWidth(option.toolbox);

  // 居中标题的右边沿 vs 工具箱左边沿
  const titleRightEdge = chartWidth / 2 + titleWidth / 2;
  const toolboxLeftEdge = chartWidth - toolboxWidth;
  const overlap = titleRightEdge - toolboxLeftEdge;

  if (overlap > 0) {
    // 将标题左移 overlap（再加 2px 间隙），等价于参考方案中的 translateX(-overlap)
    const gap = 2;
    const centeredLeftEdge = chartWidth / 2 - titleWidth / 2;
    option.title.left = centeredLeftEdge - overlap - gap;
    // left 由 "center" 改为像素值后，标题文本默认左对齐，正好实现整体左移
    chart.setOption({ title: option.title });
  }
};

const createGraphs = () => {
  for (let key in graph_configs) {
    const cfg = graph_configs[key];

    const $elem = $(key);
    $elem.empty();

    let chart = echarts.init(document.querySelector(key));

    cfg
      .data()
      .then(cfg.format)
      .then(applyMobilePieCenter.bind(null, key))
      .then((option) => {
        chart.setOption(option);
        fixMobileTitleOverlap(key, chart, option);
        // 只读柱状图数据视图（含 optionToContent）无刷新按钮，手动注入一个
        const toolbox = option.toolbox;
        const dv =
          toolbox &&
          toolbox.feature &&
          toolbox.feature.dataView;
        if (dv && dv.optionToContent && dv.readOnly) {
          attachDataViewRefreshButton(key, chart, cfg);
        }
        $(window).on("resize", function () {
          if (chart != null && chart != undefined) {
            chart.resize();
            // 移动端宽度变化后重新计算标题与工具箱是否重叠
            fixMobileTitleOverlap(key, chart, option);
          }
        });
      });
  }
};

// 为只读数据视图（readOnly:true 的柱状图）手动注入“刷新”按钮
// ECharts 在只读模式下不渲染刷新按钮，这里监听数据视图弹窗的按钮容器插入，
// 在“关闭”按钮前加一个“刷新”按钮，点击后重新拉取数据并 setOption 刷新图表，然后关闭弹窗
const attachDataViewRefreshButton = (key, chart, cfg) => {
  const container = document.querySelector(key);
  if (!container) return;

  const refresh = () => {
    // 移除数据视图弹窗 DOM（ECharts 在只读模式下未保存 _dom 引用，直接移除根节点）
    container
      .querySelectorAll('div[style*="position: absolute"][style*="top: 0"][style*="bottom: 0"]')
      .forEach((el) => el.remove());
    // 重新拉取数据并刷新图表
    cfg
      .data()
      .then(cfg.format)
      .then(applyMobilePieCenter.bind(null, key))
      .then((option) => {
        chart.setOption(option);
        fixMobileTitleOverlap(key, chart, option);
      });
  };

  const inject = (buttonContainer) => {
    if (buttonContainer.dataset.refreshInjected === "1") return;
    buttonContainer.dataset.refreshInjected = "1";
    const closeBtn = buttonContainer.querySelector("div");
    const refreshBtn = document.createElement("div");
    refreshBtn.innerHTML = _("Refresh");
    // 复用 ECharts 关闭按钮的样式（float:right 等）
    if (closeBtn) {
      refreshBtn.style.cssText = closeBtn.style.cssText;
      refreshBtn.style.marginRight = "20px";
      refreshBtn.style.cursor = "pointer";
    } else {
      refreshBtn.style.cssText =
        "float:right;margin-right:20px;border:none;cursor:pointer;padding:2px 5px;font-size:12px;border-radius:3px;background-color:#5bc0de;color:#fff;";
    }
    refreshBtn.addEventListener("click", refresh);
    // 插入到关闭按钮前
    if (closeBtn) {
      buttonContainer.insertBefore(refreshBtn, closeBtn);
    } else {
      buttonContainer.appendChild(refreshBtn);
    }
  };

  const obs = new MutationObserver((mutations) => {
    mutations.forEach((m) => {
      m.addedNodes.forEach((node) => {
        if (node.nodeType !== 1) return;
        // 数据视图的按钮容器：position:absolute;bottom:5px（移动端被 CSS 改为 15px）
        const target =
          node.style && node.style.cssText &&
          (node.style.cssText.indexOf("bottom: 5px") >= 0 ||
            node.style.cssText.indexOf("bottom:15px") >= 0)
            ? node
            : node.querySelector &&
              node.querySelector('div[style*="bottom: 5px"], div[style*="bottom:15px"]');
        if (target) inject(target);
      });
    });
  });
  obs.observe(container, { childList: true, subtree: true });
};

function updateGraphs() {
  for (let key in graph_configs) {
    const cfg = graph_configs[key];
    let chart = echarts.init(document.querySelector(key));
    cfg
      .data()
      .then(cfg.format)
      .then(applyMobilePieCenter.bind(null, key))
      .then((option) => {
        chart.setOption(option);
        fixMobileTitleOverlap(key, chart, option);
        $(window).on("resize", function () {
          if (chart != null && chart != undefined) {
            chart.resize();
            fixMobileTitleOverlap(key, chart, option);
          }
        });
      });
  }
}

$(() => {
  createGraphs();
  setInterval(updateGraphs, 300000);

  const scoreboardMatrix = Vue.extend(ScoreboardMatrix);
  // Clear the spinner
  document.querySelector("#scoreboard-matrix").innerHTML = "";
  let scoreboardMatrixContainer = document.createElement("div");
  document
    .querySelector("#scoreboard-matrix")
    .appendChild(scoreboardMatrixContainer);

  new scoreboardMatrix().$mount(scoreboardMatrixContainer);
});
