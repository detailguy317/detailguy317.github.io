/* DG317 "Sales Race" board - hand-checked numbers (no free live feed exists for automaker sales).
   Refresh once a month after automakers report (U.S. ~1st-5th, China ~1st, quarterlies ~2nd of Jan/Apr/Jul/Oct).
   Headlines under the board update by themselves (update-series robot). */
window.DG_SALES = {
  updated: "2026-11-18",
  global: {
    title: "🌍 World's biggest automakers - 2025 full year",
    note: "Toyota #1 for the 6th straight year. BYD passed Ford - the first Chinese automaker in the global top six.",
    rows: [
      ["Toyota (incl. Lexus, Daihatsu, Hino)", 11.32, "+4.7%", "TM"],
      ["Volkswagen Group", 8.98, "-0.5%", "VWAGY"],
      ["Hyundai Motor Group (Hyundai, Kia, Genesis)", 7.28, "+0.6%", "HYMTF"],
      ["General Motors", 6.18, "+3.0%", "GM"],
      ["Stellantis", 5.48, "+1.3%", "STLA"],
      ["BYD", 4.60, "", "BYDDY"]
    ],
    unit: "million vehicles",
    src: [["CarNewsChina", "https://carnewschina.com/2026/02/26/three-chinese-automakers-enter-global-top-10-as-2025-sales-rankings-finalized/"],
          ["ChinaEVHome", "https://chinaevhome.com/2026/02/12/byd-overtakes-ford-in-2025-global-sales-ranks-sixth-among-automakers/"]]
  },
  us: {
    title: "🇺🇸 U.S. sales race - Q3 2026 (Jul-Sep)",
    note: "GM still #1, but Toyota cut the gap to 37,751. Ford held #3 over Hyundai Group by under 1,200 vehicles.",
    rows: [
      ["General Motors", 670974, "-5.5%", "GM"],
      ["Toyota Motor (Toyota + Lexus)", 633223, "+0.6%", "TM"],
      ["Ford (light-duty)", 507395, "-6.6%", "F"],
      ["Hyundai Motor Group (Hyundai, Kia, Genesis)", 506200, "+5.4%", "HYMTF"]
    ],
    unit: "vehicles",
    src: [["CBT News", "https://www.cbtnews.com/gm-keeps-u-s-sales-crown/"],
          ["Ford Authority", "https://fordauthority.com/2026/10/ford-gets-third-place-narrowly-holds-off-hyundai-in-q3-2026-sales/"]]
  },
  month: {
    title: "📅 Latest month - October 2026",
    items: [
      "🇺🇸 U.S. new-vehicle sales about <b>1.3 million</b>, up about 4% from a year ago (GlobalData). Selling pace: <b>15.64 million</b> a year (SAAR, Autodata).",
      "🌍 Toyota sold a record <b>1 million</b> vehicles worldwide in one month - U.S. demand made up for China and Japan.",
      "🇨🇳 China EV makers: <b>BYD 483,125</b> · Geely 214,996 · Leapmotor 106,127 · Xpeng 50,237."
    ],
    src: [["CarPro", "https://www.carpro.com/blog/october-2026-national-auto-sales"],
          ["Haver / Autodata", "https://haver.com/articles/u-s-light-vehicle-sales-dip-in-october"],
          ["CBT News", "https://www.cbtnews.com/?p=231397"],
          ["CarNewsChina", "https://carnewschina.com/2026/11/02/china-ev-sales-in-october-byd-483125-geely-214996-leapmotor-106127-xpeng-50237/"]]
  },
  /* 🥧 Dashboard pie - U.S. sales SHARE for one quarter. Put in the units each quarter; the page works out the %.
     Everyone not listed goes in "Others". Colors stay with the brand. */
  share: {
    title: "Q3 2026",
    rows: [
      ["GM", 670413, "#ff6600"], ["Toyota", 633223, "#ffd2a8"], ["Ford", 507395, "#c2410c"],
      ["Hyundai/Kia", 506200, "#fbbf24"], ["Honda", 392341, "#7c2d12"], ["Stellantis", 324774, "#ea580c"],
      ["Nissan", 226474, "#b45309"], ["Subaru", 168538, "#fdba74"], ["Tesla", 144300, "#9ca3af"],
      ["VW Group", 134591, "#d1d5db"], ["Mazda", 108434, "#e5e7eb"], ["BMW", 106999, "#6b7280"],
      ["Mercedes", 85800, "#fde68a"],
      ["Others", 23766 + 21204 + 18543 + 18284 + 2160 + 1900 + 355 + 140 + 110, "#374151"]   // Volvo, JLR, Mitsubishi, Rivian, Polestar, INEOS, Geely, Aston, Ferrari
    ],
    note: "Some automakers (Tesla, Mercedes) don't report U.S. numbers - those are estimates.",
    src: [["GoodCarBadCar Q3 2026", "https://www.goodcarbadcar.net/2026-us-auto-sales-figures-by-manufacturer-automaker-rankings/"]]
  }
};
