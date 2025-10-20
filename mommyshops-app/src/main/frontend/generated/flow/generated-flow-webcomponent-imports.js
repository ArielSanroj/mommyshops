import { injectGlobalWebcomponentCss } from 'Frontend/generated/jar-resources/theme-util.js';

import '@vaadin/polymer-legacy-adapter/style-modules.js';
import '@vaadin/vertical-layout/src/vaadin-vertical-layout.js';
import '@vaadin/button/src/vaadin-button.js';
import '@vaadin/tooltip/src/vaadin-tooltip.js';
import 'Frontend/generated/jar-resources/disableOnClickFunctions.js';
import '@vaadin/horizontal-layout/src/vaadin-horizontal-layout.js';
import '@vaadin/vaadin-lumo-styles/sizing.js';
import '@vaadin/vaadin-lumo-styles/spacing.js';
import '@vaadin/vaadin-lumo-styles/style.js';
import '@vaadin/vaadin-lumo-styles/vaadin-iconset.js';
import '@vaadin/common-frontend/ConnectionIndicator.js';
import 'Frontend/generated/jar-resources/ReactRouterOutletElement.tsx';

const loadOnDemand = (key) => {
  const pending = [];
  if (key === '5e7b7977cc1e99e3addf8b1038b344370df78b7335c13fbc594fda86fb596902') {
    pending.push(import('./chunks/chunk-2e900625e0d6a883b1761b33550a1b1949cfc49e0ecba752070d60d281cb8906.js'));
  }
  if (key === '8adffa95bfa26bf0099b04b3c7875b62ddf94ee13b8ba1ab3a983cbac102981a') {
    pending.push(import('./chunks/chunk-6aa3ea549496c45470afc93538d8e35f686c73038b5930b3e021aa04e961ef48.js'));
  }
  if (key === 'e319aa355b09d1941e33291038b9a5a9deeb726b7edede87f70b65b816aacf59') {
    pending.push(import('./chunks/chunk-c9f87bf012e78d5dada4b36bd1d216cb6be68c91a0dc6a267d677295e8ed7849.js'));
  }
  return Promise.all(pending);
}

window.Vaadin = window.Vaadin || {};
window.Vaadin.Flow = window.Vaadin.Flow || {};
window.Vaadin.Flow.loadOnDemand = loadOnDemand;
window.Vaadin.Flow.resetFocus = () => {
 let ae=document.activeElement;
 while(ae&&ae.shadowRoot) ae = ae.shadowRoot.activeElement;
 return !ae || ae.blur() || ae.focus() || true;
}