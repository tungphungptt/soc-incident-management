

export const money=(value:any)=>value===null||value===undefined?'Chưa cấu hình':Number(value).toLocaleString('vi-VN')+' ₫';

export const date=(value:any)=>value?new Date(value.endsWith?.('Z')?value:value+'Z').toLocaleString('vi-VN'):'—';
