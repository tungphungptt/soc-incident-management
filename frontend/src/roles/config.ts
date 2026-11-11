

export const roleConfig:Record<string,{title:string;label:string;accent:string;subtitle:string}>= {
 ADMIN:{title:'Quản trị hệ thống',label:'Admin',accent:'#8b5cf6',subtitle:'Danh tính · Danh mục · Kiểm soát truy cập'},
 SOC_MANAGER:{title:'Trung tâm điều hành',label:'SOC Manager',accent:'#3b82f6',subtitle:'Rủi ro tổ chức · Hiệu suất · Phân công'},
 SOC_L1:{title:'Hàng đợi phân loại',label:'SOC Analyst L1',accent:'#06b6d4',subtitle:'Phát hiện sớm · Ưu tiên SLA · Chuyển cấp'},
 SOC_L2:{title:'Bàn điều tra',label:'SOC Analyst L2',accent:'#f59e0b',subtitle:'Bằng chứng · Tương quan IOC · Khoanh vùng'},
 SOC_L3:{title:'Phòng phân tích chuyên sâu',label:'SOC Analyst L3',accent:'#ec4899',subtitle:'Critical / High · Kỹ thuật tấn công · Phân tích'},
 INCIDENT_RESPONDER:{title:'Trung tâm ứng phó',label:'Incident Responder',accent:'#f97316',subtitle:'Cô lập · Khắc phục · Phục hồi'},
 THREAT_HUNTER:{title:'Không gian săn mối đe dọa',label:'Threat Hunter',accent:'#10b981',subtitle:'IOC · MITRE ATT&CK · Phát hiện mới'},
};
