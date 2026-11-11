import {ReactNode, useId, useMemo, useState} from 'react';
import {ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight, Search, SlidersHorizontal, X} from 'lucide-react';
import {Row} from '../types';
import {Button} from './Button';
import {EmptyState} from './States';

type Column = {key: string; label: string; render?: (row: Row) => ReactNode};
type Pagination = {page: number; pageSize: number; total: number; onPageChange: (page: number) => void};
type Props = {rows: Row[]; columns: Column[]; empty?: string; onRow?: (row: Row) => void; pagination?: Pagination};
const searchable = (value: unknown) => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLocaleLowerCase('vi');
const filterKeys = new Set(['TrangThai', 'MucDoNghiemTrong', 'LoaiIOC', 'MucDoTinCay', 'VaiTro', 'role']);
const collator = new Intl.Collator('vi', {numeric: true, sensitivity: 'base'});

export function DataTable({rows, columns, empty = 'Chưa có dữ liệu', onRow, pagination}: Props) {
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('');
  const [sort, setSort] = useState<{key: string; direction: 1 | -1} | null>(null);
  const searchId = useId();
  const filterId = useId();
  const filtering = columns.find(column => filterKeys.has(column.key) && new Set(rows.map(row => row[column.key])).size > 1);
  const values = filtering ? [...new Set(rows.map(row => row[filtering.key]).filter(value => value != null))].sort((a, b) => collator.compare(String(a), String(b))) : [];
  const displayed = useMemo(() => {
    const visible = rows.map((row, sourceIndex) => ({row, sourceIndex})).filter(({row}) =>
      (!query || columns.some(column => {
        const value = row[column.key];
        return value != null && searchable(typeof value === 'object' ? JSON.stringify(value) : value).includes(searchable(query));
      })) && (!filtering || !filter || String(row[filtering.key]) === filter));
    if (sort) visible.sort((a, b) => {
      const left = a.row[sort.key], right = b.row[sort.key];
      return sort.direction * (typeof left === 'number' && typeof right === 'number' ? left - right : collator.compare(String(left ?? ''), String(right ?? '')));
    });
    return visible;
  }, [rows, columns, query, filter, filtering?.key, sort]);
  const controls = rows.length > 8 || !!query || !!filter || !!pagination;
  const sortable = (key: string) => rows.some(row => ['number', 'string', 'boolean'].includes(typeof row[key]));
  const changeSort = (key: string) => setSort(current => current?.key === key ? current.direction === 1 ? {key, direction: -1} : null : {key, direction: 1});
  const pageCount = pagination ? Math.max(1, Math.ceil(pagination.total / pagination.pageSize)) : 1;
  return <div className="ui-data-table">
    {controls && <div className="ui-table-toolbar">
      <label className="ui-table-search" htmlFor={searchId}><Search size={18} aria-hidden="true"/><span className="ui-sr-only">{pagination ? 'Tìm trong trang đã tải' : 'Tìm trong bảng'}</span><input id={searchId} type="search" value={query} placeholder={pagination ? 'Tìm trong trang đã tải…' : 'Tìm trong bảng…'} onChange={event => setQuery(event.target.value)}/></label>
      {filtering && <label className="ui-table-filter" htmlFor={filterId}><SlidersHorizontal size={16} aria-hidden="true"/><span className="ui-sr-only">Lọc {filtering.label}</span><select id={filterId} aria-label={`Lọc ${filtering.label}`} value={filter} onChange={event => setFilter(event.target.value)}><option value="">{filtering.label}: Tất cả</option>{values.map(value => <option key={String(value)} value={String(value)}>{String(value)}</option>)}</select></label>}
      {(query || filter || sort) && <Button variant="ghost" onClick={() => {setQuery(''); setFilter(''); setSort(null);}}><X size={16}/>Bỏ lọc / sắp xếp</Button>}
      <span className="ui-table-count" role="status">{displayed.length}/{rows.length} dòng đã tải</span>
    </div>}
    <div className="w-table-scroll" tabIndex={0} role="region" aria-label="Bảng dữ liệu, có thể cuộn ngang"><table className="w-table"><thead><tr>{columns.map(column => <th key={column.key} scope="col" aria-sort={sort?.key === column.key ? sort.direction === 1 ? 'ascending' : 'descending' : undefined}>
      {sortable(column.key) ? <button type="button" className="ui-sort-button" onClick={() => changeSort(column.key)} aria-label={`Sắp xếp theo ${column.label}`}>{column.label}{sort?.key === column.key ? sort.direction === 1 ? <ArrowUp size={14}/> : <ArrowDown size={14}/> : <ArrowUpDown size={14}/>}</button> : column.label}
    </th>)}</tr></thead><tbody>{displayed.map(({row, sourceIndex}) => <tr key={sourceIndex} onClick={() => onRow?.(row)} className={onRow ? 'clickable' : ''} tabIndex={onRow ? 0 : undefined} onKeyDown={onRow ? event => {if (event.target === event.currentTarget && (event.key === 'Enter' || event.key === ' ')) {event.preventDefault(); onRow(row);}} : undefined}>{columns.map(column => <td key={column.key}>{column.render ? column.render(row) : row[column.key] == null ? '—' : typeof row[column.key] === 'object' ? JSON.stringify(row[column.key]) : String(row[column.key])}</td>)}</tr>)}</tbody></table>
      {!displayed.length && <EmptyState message={rows.length ? 'Không có kết quả phù hợp. Thử thay đổi từ khóa hoặc bộ lọc.' : empty}/>}
    </div>
    {pagination && <div className="ui-table-pagination"><span>Trang {pagination.page}/{pageCount} · {pagination.total} bản ghi</span><div><Button aria-label="Trang trước" disabled={pagination.page <= 1} onClick={() => pagination.onPageChange(pagination.page - 1)}><ChevronLeft size={16}/>Trước</Button><Button aria-label="Trang sau" disabled={pagination.page >= pageCount} onClick={() => pagination.onPageChange(pagination.page + 1)}>Sau<ChevronRight size={16}/></Button></div></div>}
  </div>;
}
