/* DG317 Deals & Incentives - hand-checked links (CarStuff -> Deals tab).
   Every link goes to the automaker's OWN site. Offers change by month and ZIP, so we link to the official page
   instead of copying prices. Re-check once a month: open each link, fix any that moved, change "checked". */
window.DG_DEALS = {
  checked: "2026-11-25",
  brands: [
    // [name, link, true = goes straight to the offers page (checked) / false = official site (tap Offers there)]
    ["Ford", "https://www.ford.com", false],
    ["Lincoln", "https://www.lincoln.com", false],
    ["Chevrolet", "https://www.chevrolet.com/current-offers", true],
    ["GMC", "https://www.gmc.com", false],
    ["Buick", "https://www.buick.com", false],
    ["Cadillac", "https://www.cadillac.com", false],
    ["GM (all brands)", "https://www.gmfinancial.com/en-us/lease-or-buy/current-offers.html", true],
    ["Ram", "https://www.ramtrucks.com/incentives.html", true],
    ["Jeep", "https://www.jeep.com/incentives.html", true],
    ["Dodge", "https://www.dodge.com", false],
    ["Chrysler", "https://www.chrysler.com", false],
    ["Toyota", "https://www.toyota.com/deals-incentives/", true],
    ["Lexus", "https://www.lexus.com", false],
    ["Honda", "https://automobiles.honda.com/tools/current-offers", true],
    ["Acura", "https://www.acura.com", false],
    ["Hyundai", "https://www.hyundaiusa.com/us/en/offers", true],
    ["Kia", "https://www.kia.com/us/en/offers", true],
    ["Nissan", "https://www.nissanusa.com", false],
    ["Subaru", "https://www.subaru.com/shopping-tools/special-offers.html", true],
    ["Mazda", "https://www.mazdausa.com", false],
    ["Volkswagen", "https://www.vw.com", false],
    ["Tesla", "https://www.tesla.com", false]
  ],
  programs: [
    // [name, who it's for, link ("" = ask the dealer)]
    ["Ford X-Plan (Partner Recognition)", "Employees, retirees and spouses of Ford partner companies (suppliers, fleets, some clubs and groups). Get your partner code from HR or your group, then make a PIN.", "https://www.fordpartner.com"],
    ["GM Supplier Discount", "Employees of GM supplier companies. Get the company code from HR, register, then get an authorization number. Works with most current offers.", "https://www.gmsupplierdiscount.com"],
    ["GMC / GM discount programs", "GM's list of special programs (supplier, military, first responders, college and more).", "https://www.gmc.com/discount-programs"],
    ["Stellantis Affiliate Rewards", "Employees of Stellantis partner companies (Chrysler, Dodge, Jeep, Ram, Fiat). Ask your HR, then tell the dealer up front.", ""],
    ["Military & first responder", "Most brands offer extra cash for active duty, veterans, police, fire and EMS. Ask for it by name. It often stacks with other offers.", ""],
    ["College grad", "Recent and soon-to-be grads can often add a rebate on top of current offers. Bring proof of graduation.", ""],
    ["Loyalty & conquest", "Extra cash for staying with a brand (loyalty) or for trading in another brand's vehicle (conquest). Ask what's running in your ZIP.", ""]
  ]
};
