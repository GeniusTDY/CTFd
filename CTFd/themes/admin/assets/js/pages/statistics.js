import "./main";
import CTFd from "../compat/CTFd";
import $ from "jquery";
import echarts from "echarts/dist/echarts.common";
import { colorHash } from "../compat/styles";
import Vue from "vue";
import ScoreboardMatrix from "../components/statistics/ScoreboardMatrix.vue";

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
            dataView: { show: true, readOnly: false },
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
            dataView: { show: true, readOnly: false },
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
            dataView: { show: true, readOnly: false },
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
            dataView: { show: true, readOnly: false },
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
            dataView: { show: true, readOnly: false },
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
            dataView: { show: true, readOnly: false },
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

// 移动端下「各题目解题百分比」图表标题过长会与右上角工具箱图标重叠
// 仅在小屏幕（<=767.98px）生效：测量标题文本宽度与工具箱占据宽度，
// 计算居中标题右边沿与工具箱左边沿的重叠量，若重叠则将标题左移该重叠量（参考 translateX(-overlap) 方案）
// 桌面端宽度充足，不做任何改动
const MOBILE_BP = "(max-width: 767.98px)";
const solvePercentagesKey = "#solve-percentages-graph";

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
// 仅作用于「各题目解题百分比」图表，不影响其它图表与桌面端
const fixSolvePercentagesTitleOverlap = (key, chart, option) => {
  if (key !== solvePercentagesKey) return;
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
        fixSolvePercentagesTitleOverlap(key, chart, option);
        $(window).on("resize", function () {
          if (chart != null && chart != undefined) {
            chart.resize();
            // 移动端宽度变化后重新计算标题与工具箱是否重叠
            fixSolvePercentagesTitleOverlap(key, chart, option);
          }
        });
      });
  }
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
        fixSolvePercentagesTitleOverlap(key, chart, option);
        $(window).on("resize", function () {
          if (chart != null && chart != undefined) {
            chart.resize();
            fixSolvePercentagesTitleOverlap(key, chart, option);
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
