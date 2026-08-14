# =============================================================================
# 水合离子簇 VMD 可视化（CPK）
# -----------------------------------------------------------------------------
# 前置：先跑 simul_analysis.ipynb 第 4 节，或：
#   python _extract_hydrated_ions.py --ion-sel "type 1" --ion-label Mg --cutoff 3.2
#
# 用法：
#   启动时：  vmd -e vmd.tcl -args Mg01
#             vmd -e vmd.tcl -args Cl01 hydrated_ion/Cl01_f0000.xyz
#   已打开 VMD 控制台（不要写 source … -args）：
#             set ion_tag Cl01;  source vmd.tcl
#             set argv {Mg01};   source vmd.tcl
#             set xyz_one hydrated_ion/Mg01_f0000.xyz; source vmd.tcl
#
# 文件：hydrated_ion/{Ion}{ii}_f{frame}.xyz
# 表示：整簇 CPK（球棍，按元素着色）；第一原子为中心离子。
# =============================================================================

# ----- 可调（若已在控制台 set 过则保留，不被默认值覆盖）-----
if {![info exists hyd_dir]} { set hyd_dir "hydrated_ion" }
if {![info exists ion_tag]} { set ion_tag "Mg01" }
if {![info exists xyz_one]} { set xyz_one "" }

# 启动参数优先：vmd -e vmd.tcl -args [ion_tag] [optional_single_xyz]
# 控制台也可：set argv {Cl01}; source vmd.tcl
if {[info exists argv] && [llength $argv] >= 1 && [lindex $argv 0] ne ""} {
  set ion_tag [lindex $argv 0]
}
if {[info exists argv] && [llength $argv] >= 2 && [lindex $argv 1] ne ""} {
  set xyz_one [lindex $argv 1]
}

color change rgb  0 0.122 0.467 0.706
color change rgb  1 0.70  0.20  0.10
color change rgb  2 0.40  0.40  0.40
color change rgb  3 0.70  0.40  0.00
color change rgb  4 0.74  0.74  0.13
color change rgb  7 0.17  0.63  0.17
color change rgb  9 0.89  0.47  0.76
color change rgb 10 0.09  0.75  0.81
color change rgb 11 0.58  0.40  0.74
color Element Mg purple
color Element Cl green

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

color change rgb  0 0.122 0.467 0.706
color change rgb  1 0.70  0.20  0.10
color change rgb 11 0.58  0.40  0.74
color Element O red
color Element H white
color Element Mg purple
color Element Cl green

menu main on
display projection Perspective
axes location Off
color Display Background white
display depthcue off

material change ambient   Diffuse 0.00
material change specular  Diffuse 0.05
material change diffuse   Diffuse 0.90
material change shininess Diffuse 0

if {[molinfo num] > 0} {
  mol delete all
}

# ----- 收集要读的 XYZ -----
set files {}
if {$xyz_one ne ""} {
  if {![file exists $xyz_one]} {
    puts "ERROR: $xyz_one not found."
    return
  }
  set files [list $xyz_one]
} else {
  if {![file isdirectory $hyd_dir]} {
    puts "ERROR: directory $hyd_dir missing. Extract hydrated ions first."
    return
  }
  set pattern [file join $hyd_dir "${ion_tag}_f*.xyz"]
  set files [lsort -dictionary [glob -nocomplain $pattern]]
  if {[llength $files] == 0} {
    puts "ERROR: no files match $pattern"
    puts "  available prefixes:"
    array set seen {}
    foreach f [lsort -dictionary [glob -nocomplain [file join $hyd_dir "*_f*.xyz"]]] {
      set b [file tail $f]
      if {[regexp {^([A-Za-z]+[0-9]+)_f} $b -> pref]} {
        if {![info exists seen($pref)]} {
          set seen($pref) 1
          puts "    $pref"
        }
      }
    }
    return
  }
}

set first [lindex $files 0]
mol new $first type xyz waitfor all
mol rename top "C07_${ion_tag}"

foreach f [lrange $files 1 end] {
  mol addfile $f type xyz waitfor all
}

set numatom  [molinfo top get numatoms]
set numframe [molinfo top get numframes]
puts "loaded [llength $files] XYZ → $numatom atoms, $numframe frame(s)"
puts "  first: $first"
if {$numframe > 1} {
  puts "  last:  [lindex $files end]"
}

while {[molinfo top get numreps] > 0} {
  mol delrep 0 top
}

# Display（小簇：略拉近）
display height 1.0
display distance -2.0
display shadows on
display ambientocclusion on
display aoambient 0.85
display aodirect 0.15

# 整簇 CPK：球半径×VDW、键半径、球/键分辨率
mol selection "all"
mol addrep top
mol modstyle 0 top CPK 1.0 0.3 60 60
mol modcolor 0 top Element
mol modmaterial 0 top Diffuse
mol selupdate 0 top on

# 中心离子略放大（XYZ 第一原子 = 离子）
mol selection "index 0"
mol addrep top
mol modstyle 1 top VDW 0.5 60
mol modcolor 1 top Element
mol modmaterial 1 top Diffuse
mol selupdate 1 top on

display resetview
scale by 0.3

render options POV3 {/opt/homebrew/bin/povray +W%w +H%h -I%s -O%s.png +X +A +FN +UA}

puts "CPK view ready. Animate frames in VMD if multiple XYZ were loaded."
puts "  tip: vmd -e vmd.tcl -args Cl01"
