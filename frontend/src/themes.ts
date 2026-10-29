export const themes=[
  {id:'soft-charcoal',name:'Soft charcoal',dark:true,color:'#91b9ad'},
  {id:'corporate-navy',name:'Corporate navy',dark:false,color:'#244b78'},
  {id:'corporate-steel',name:'Corporate steel',dark:false,color:'#4b6278'},
  {id:'corporate-teal',name:'Corporate teal',dark:false,color:'#126d73'},
  {id:'corporate-burgundy',name:'Corporate burgundy',dark:false,color:'#823b50'},
  {id:'graphite',name:'Graphite dark',dark:true,color:'#b9c9db'},
  {id:'clear-white',name:'Clear white',dark:false,color:'#174c9c'},
  {id:'forest',name:'Forest light',dark:false,color:'#246a53'},
  {id:'forest-dark',name:'Forest dark',dark:true,color:'#7ed6ae'},
  {id:'ocean',name:'Ocean',dark:false,color:'#096d9d'},
  {id:'midnight',name:'Midnight',dark:true,color:'#83c9ff'},
  {id:'plum',name:'Plum',dark:false,color:'#8546a1'},
  {id:'amethyst',name:'Amethyst',dark:true,color:'#d5adff'},
  {id:'sand',name:'Sand',dark:false,color:'#946127'},
  {id:'slate',name:'Slate',dark:false,color:'#475e85'},
] as const;
export function resolveTheme(value:string|null,legacy:string|null=null){return themes.find(t=>t.id===value)?.id||(legacy==='dark'?'forest-dark':'forest');}
export function appearanceTheme(value:string|null,legacy:string|null=null){const id=resolveTheme(value,legacy);return themes.find(t=>t.id===id)?.dark?'soft-charcoal':'corporate-navy';}
export function savedTheme(){try{return appearanceTheme(localStorage.getItem('callatlas-theme'),localStorage.getItem('theme'));}catch{return appearanceTheme(null);}}
export function applyTheme(id:string){const theme=themes.find(t=>t.id===id)||themes[0];document.documentElement.dataset.palette=theme.id;document.documentElement.dataset.theme=theme.dark?'dark':'light';document.documentElement.style.colorScheme=theme.dark?'dark':'light';}
