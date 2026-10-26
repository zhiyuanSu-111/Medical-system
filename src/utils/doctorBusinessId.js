/**
 * 与后端 database.doctor_business_id 一致：6 位业务工号
 * 100000 + 顶层科室 ID(1–99)×100 + 科内序号(1–999)
 */
export function doctorBusinessId(departmentId, sequence = 1) {
  if (departmentId < 1 || departmentId > 99 || sequence < 1 || sequence > 999) {
    throw new Error('departmentId 须在 1..99，sequence 须在 1..999')
  }
  return 100000 + departmentId * 100 + sequence
}
