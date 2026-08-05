# =============================================================================
# COF 膜–水–Na · VMD 可视化
# -----------------------------------------------------------------------------
# 用法（在含下列文件的目录）：
#   result_atoms.xyz
#   result_box.dat
#   result_connect.dat   — 可选；有则用拓扑键替换 VMD 猜键
#   vmd -e vmd.tcl
#
# 原子顺序（COF → 水 → Na）：
#   COF  810  = 5 × 162     → index 0 .. 809
#   水  3000  = 1000 × 3    → index 810 .. 3809
#   Na    30                → index 3810 .. 3839
# 改装盒份数时改 ncof / nwat / nion。
#
# 表示：COF / Na = VDW 0.5@60；水 = Licorice 0.2@60（需 connect 更准；
# 跨盒切开时 Licorice 可能出现长键，见文章 §六–七）。
# =============================================================================

set ncof 810
set nwat 3000
set nion 30
set iwat0 $ncof
set iwat1 [expr {$ncof + $nwat - 1}]
set ion0  [expr {$ncof + $nwat}]
set ion1  [expr {$ncof + $nwat + $nion - 1}]

color change rgb  0 0.122 0.467 0.706
color change rgb  1 0.70  0.20  0.10
color change rgb  2 0.40  0.40  0.40
color change rgb  3 0.70  0.40  0.00
color change rgb  4 0.74  0.74  0.13
color change rgb  7 0.17  0.63  0.17
color change rgb  9 0.89  0.47  0.76
color change rgb 10 0.09  0.75  0.81
color change rgb 11 0.58  0.40  0.74
color Element C gray
color Element N blue
color Element O red
color Element S yellow
color Element H white
color Element Na purple

menu main on
display projection Perspective
axes location Off
color Display Background white
display depthcue off

material change ambient   Diffuse 0.00
material change specular  Diffuse 0.05
material change diffuse   Diffuse 0.90
material change shininess Diffuse 0.55
material change opacity   Diffuse 1.0

if {[molinfo num] > 0} {
  mol delete all
}

set fname "result_atoms.xyz"
if {![file exists $fname]} {
  puts "ERROR: $fname not found. Export it from simul_analysis.ipynb first."
  return
}
mol new $fname type xyz waitfor all
mol rename top "C06_COF_water_Na"

set numatom  [molinfo top get numatoms]
set numframe [molinfo top get numframes]
puts "loaded $fname : $numatom atoms, $numframe frame(s)"
if {$numatom != [expr {$ncof + $nwat + $nion}]} {
  puts "WARNING: atom count $numatom != ncof+nwat+nion=[expr {$ncof+$nwat+$nion}]; check selections."
}

# 若有 connect：清掉 XYZ 猜键，按 CONECT（1-based = 文件顺序）重建
set cname "result_connect.dat"
if {[file exists $cname]} {
  package require topotools
  topo clearbonds
  set fp [open $cname r]
  set nbond 0
  while {[gets $fp line] >= 0} {
    if {![string match "CONECT*" [string trim $line]]} { continue }
    set ids [lrange [string trim $line] 1 end]
    if {[llength $ids] < 2} { continue }
    set a0 [expr {[lindex $ids 0] - 1}]
    foreach a1s [lrange $ids 1 end] {
      set a1 [expr {$a1s - 1}]
      if {$a0 < $a1} {
        topo addbond $a0 $a1
        incr nbond
      }
    }
  }
  close $fp
  mol reanalyze top
  puts "loaded $cname : $nbond bonds (replaced distance-guessed bonds)"
} else {
  puts "NOTE: $cname missing; VMD keeps distance-guessed bonds (water Licorice may mis-bond)."
}

while {[molinfo top get numreps] > 0} {
  mol delrep 0 top
}

# Display Settings（须在 scale / rotate 前设好）
display height 1.0
display distance -1.0
display shadows on
display ambientocclusion on
display aoambient 0.85
display aodirect 0.15

rotate z by 90
rotate y by -90
scale by 0.3

# 0 — COF：VDW 0.5，分辨率 60
mol selection "index 0 to [expr {$ncof - 1}]"
mol addrep top
mol modstyle 0 top VDW 0.5 60
mol modcolor 0 top Element
mol modmaterial 0 top Diffuse
mol selupdate 0 top on

# 1 — 水：Licorice 0.2，分辨率 60（整分子 O+H）
mol selection "index $iwat0 to $iwat1"
mol addrep top
mol modstyle 1 top Licorice 0.2 60 60
mol modcolor 1 top Element
mol modmaterial 1 top Diffuse
mol selupdate 1 top on

# 2 — Na⁺：VDW 0.5，分辨率 60
mol selection "index $ion0 to $ion1"
mol addrep top
mol modstyle 2 top VDW 0.5 60
mol modcolor 2 top ColorID 11
mol modmaterial 2 top Diffuse
mol selupdate 2 top on

set fname "result_box.dat"
if {[file exists $fname]} {
  set in [open $fname r]
  set cell {}
  while {[gets $in line] != -1} {
    if {[string trim $line] eq ""} { continue }
    lappend cell $line
  }
  close $in
  if {[llength $cell] > 0} {
    pbc set $cell -all
    pbc box -center origin -color gray -width 0.3
  }
} else {
  puts "WARNING: result_box.dat missing; skip pbc box."
}

render options POV3 {/opt/homebrew/bin/povray +W%w +H%h -I%s -O%s.png +X +A +FN +UA}
