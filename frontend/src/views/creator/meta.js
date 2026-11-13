import moment from 'moment'

export const ORDER_STATUS = { 0: '草稿', 1: '待审核', 2: '已驳回', 3: '已上线', 4: '进行中', 5: '已完成', 6: '已关闭' }
export const ORDER_STATUS_CLASS = {
  0: 'bg-gray-100 text-gray-500',
  1: 'bg-amber-50 text-amber-600',
  2: 'bg-red-50 text-xhs-red',
  3: 'bg-emerald-50 text-emerald-600',
  4: 'bg-blue-50 text-blue-600',
  5: 'bg-emerald-50 text-emerald-700',
  6: 'bg-gray-100 text-gray-400',
}
export const DELIVERY_STATUS = { 0: '待审核', 1: '已通过', 2: '退回修改' }
export const DELIVERY_STATUS_CLASS = {
  0: 'bg-amber-50 text-amber-600',
  1: 'bg-emerald-50 text-emerald-600',
  2: 'bg-red-50 text-xhs-red',
}
export const DELIVERY_TYPE = { 0: '视频', 1: '外链' }

export const formatTime = (t) => (t ? moment(t).format('YYYY-MM-DD HH:mm') : '-')

export const formatSize = (bytes) => {
  if (!bytes && bytes !== 0) return '-'
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
}