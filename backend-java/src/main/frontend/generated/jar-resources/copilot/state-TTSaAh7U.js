import { am as u, an as l } from "./copilot-BVlb74ld.js";
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const p = { attribute: !0, type: String, converter: l, reflect: !1, hasChanged: u }, d = (t = p, a, e) => {
  const { kind: o, metadata: s } = e;
  let n = globalThis.litPropertyMetadata.get(s);
  if (n === void 0 && globalThis.litPropertyMetadata.set(s, n = /* @__PURE__ */ new Map()), n.set(e.name, t), o === "accessor") {
    const { name: r } = e;
    return { set(i) {
      const c = a.get.call(this);
      a.set.call(this, i), this.requestUpdate(r, c, t);
    }, init(i) {
      return i !== void 0 && this.P(r, void 0, t), i;
    } };
  }
  if (o === "setter") {
    const { name: r } = e;
    return function(i) {
      const c = this[r];
      a.call(this, i), this.requestUpdate(r, c, t);
    };
  }
  throw Error("Unsupported decorator location: " + o);
};
function h(t) {
  return (a, e) => typeof e == "object" ? d(t, a, e) : ((o, s, n) => {
    const r = s.hasOwnProperty(n);
    return s.constructor.createProperty(n, r ? { ...o, wrapped: !0 } : o), r ? Object.getOwnPropertyDescriptor(s, n) : void 0;
  })(t, a, e);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function g(t) {
  return h({ ...t, state: !0, attribute: !1 });
}
export {
  h as n,
  g as r
};
