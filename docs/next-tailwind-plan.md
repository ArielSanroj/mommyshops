# Plan de migración a Next.js + Tailwind

Este es el blueprint resumido para mover Mommyshops Analyzer al stack recomendado (Next.js 14 + Tailwind CSS + Vercel):

1. **Estructura del proyecto**
   - `apps/web` (Next.js App Router, TypeScript, Tailwind, ESLint, Prettier)
   - `packages/ui` (componentes compartidos: tarjetas, botones, badges, sliders)
   - `packages/config` (tokens de color, tipografía, theming limpio)

2. **Rutas sugeridas**
   - `/` Homepage remodelada (hero, flujo 4 pasos, casos)
   - `/analyzer` (flujo actual de análisis; hidratar mediante Server Actions)
   - `/labs/[id]` (detalle de fórmula generada)
   - `/api` proxys para backend Python mientras se refactoriza

3. **Tailwind Theme**
   ```ts
   // tailwind.config.ts
   extend: {
     colors: {
       brand: {
         DEFAULT: '#7C3AED',
         accent: '#F472B6',
         peach: '#FDB8C6',
         mint: '#A9E2C5',
         ink: '#0F172A',
       }
     },
     fontFamily: {
       sans: ['DM Sans', 'Inter', 'system-ui']
     }
   }
   ```

4. **Roadmap**
   - [ ] Exportar componentes actuales como módulos de React (Hero, JourneyGrid, Pillars, Analyzer shell)
   - [ ] Reemplazar estilos CSS por utilidades Tailwind + variantes accesibles
   - [ ] Configurar `next-seo` + `@next/font` + `next/image`
   - [ ] Medir Core Web Vitals en Vercel Preview y optimizar

5. **SEO/Performance**
   - Implementar metadata dinámica vía `generateMetadata`
   - SSR para hero/landing, CSR para Analyzer
   - Edge caching en Vercel para secciones estáticas

Este documento sirve como checklist cuando el equipo esté listo para ejecutar la migración completa.
