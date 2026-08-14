// 
// Molecular graphics export from VMD 2.0b1
// http://www.ks.uiuc.edu/Research/vmd/
// Requires POV-Ray 3.5 or later
// 
// POV 3.x input script : vmdscene.pov 
// try povray +W1024 +H1024 -Ivmdscene.pov -Ovmdscene.pov.tga +P +X +A +FT +C
#if (version < 3.5) 
#error "VMD POV3DisplayDevice has been compiled for POV-Ray 3.5 or above.\nPlease upgrade POV-Ray or recompile VMD."
#end 
#declare VMD_clip_on=array[3] {0, 0, 0};
#declare VMD_clip=array[3];
#declare VMD_scaledclip=array[3];
#declare VMD_line_width=0.0020;
#macro VMDC ( C1 )
  texture { pigment { rgbt C1 }}
#end
#macro VMD_point (P1, R1, C1)
  #local T = texture { finish { ambient 1.0 diffuse 0.0 phong 0.0 specular 0.0 } pigment { C1 } }
  #if(VMD_clip_on[2])
  intersection {
    sphere {P1, R1 texture {T} #if(VMD_clip_on[1]) clipped_by {VMD_clip[1]} #end }
    VMD_clip[2]
  }
  #else
  sphere {P1, R1 texture {T} #if(VMD_clip_on[1]) clipped_by {VMD_clip[1]} #end }
  #end
#end
#macro VMD_line (P1, P2, C1)
  #local T = texture { finish { ambient 1.0 diffuse 0.0 phong 0.0 specular 0.0 } pigment { C1 } }
  #if(VMD_clip_on[2])
  intersection {
    cylinder {P1, P2, VMD_line_width texture {T} #if(VMD_clip_on[1]) clipped_by {VMD_clip[1]} #end }
    VMD_clip[2]
  }
  #else
  cylinder {P1, P2, VMD_line_width texture {T} #if(VMD_clip_on[1]) clipped_by {VMD_clip[1]} #end }
  #end
#end
#macro VMD_sphere (P1, R1, C1)
  #local T = texture { pigment { C1 } }
  #if(VMD_clip_on[2])
  intersection {
    sphere {P1, R1 texture {T} #if(VMD_clip_on[1]) clipped_by {VMD_clip[1]} #end }
    VMD_clip[2]
  }
  #else
  sphere {P1, R1 texture {T} #if(VMD_clip_on[1]) clipped_by {VMD_clip[1]} #end }
  #end
#end
#macro VMD_cylinder (P1, P2, R1, C1, O1)
  #local T = texture { pigment { C1 } }
  #if(VMD_clip_on[2])
  intersection {
    cylinder {P1, P2, R1 #if(O1) open #end texture {T} #if(VMD_clip_on[1]) clipped_by {VMD_clip[1]} #end }
    VMD_clip[2]
  }
  #else
  cylinder {P1, P2, R1 #if(O1) open #end texture {T} #if(VMD_clip_on[1]) clipped_by {VMD_clip[1]} #end }
  #end
#end
#macro VMD_cone (P1, P2, R1, C1)
  #local T = texture { pigment { C1 } }
  #if(VMD_clip_on[2])
  intersection {
    cone {P1, R1, P2, VMD_line_width texture {T} #if(VMD_clip_on[1]) clipped_by {VMD_clip[1]} #end }
    VMD_clip[2]
  }
  #else
  cone {P1, R1, P2, VMD_line_width texture {T} #if(VMD_clip_on[1]) clipped_by {VMD_clip[1]} #end }
  #end
#end
#macro VMD_triangle (P1, P2, P3, N1, N2, N3, C1)
  #local T = texture { pigment { C1 } }
  smooth_triangle {P1, N1, P2, N2, P3, N3 texture {T} #if(VMD_clip_on[1]) clipped_by {VMD_clip[1]} #end }
#end
#macro VMD_tricolor (P1, P2, P3, N1, N2, N3, C1, C2, C3)
  #local NX = P2-P1;
  #local NY = P3-P1;
  #local NZ = vcross(NX, NY);
  #local T = texture { pigment {
    average pigment_map {
      [1 gradient x color_map {[0 rgb 0] [1 C2*3]}]
      [1 gradient y color_map {[0 rgb 0] [1 C3*3]}]
      [1 gradient z color_map {[0 rgb 0] [1 C1*3]}]
    }
    matrix <1.01,0,1,0,1.01,1,0,0,1,-.002,-.002,-1>
    matrix <NX.x,NX.y,NX.z,NY.x,NY.y,NY.z,NZ.x,NZ.y,NZ.z,P1.x,P1.y,P1.z>
  } }
  smooth_triangle {P1, N1, P2, N2, P3, N3 texture {T} #if(VMD_clip_on[1]) clipped_by {VMD_clip[1]} #end }
#end
camera {
  up <0, 1.0000, 0>
  right <1.0000, 0, 0>
  location <0.0000, 0.0000, -2.0000>
  look_at <0.0000, 0.0000, -0.0000>
  direction <-0.0000, -0.0000, 4.0000>
}
light_source { 
  <-0.1000, 0.1000, -1.0000> 
  color rgb<1.000, 1.000, 1.000> 
  parallel 
  point_at <0.0, 0.0, 0.0> 
}
light_source { 
  <1.0000, 2.0000, -0.5000> 
  color rgb<1.000, 1.000, 1.000> 
  parallel 
  point_at <0.0, 0.0, 0.0> 
}
background {
  color rgb<1.000, 1.000, 1.000>
}
#default { texture {
 finish { ambient 0.000 diffuse 0.650 phong 0.1 phong_size 40.000 specular 0.500 }
} }
#declare VMD_line_width=0.0020;
#default { texture {
 finish { ambient 0.000 diffuse 0.900 phong 0.1 phong_size 1.000 specular 0.050 }
} }
// Mol[1] Rep[0] CPK
// Mol[1] Rep[0] VDW
VMD_sphere(<0.0047,0.0078,-0.0102>,0.0321,rgbt<0.170,0.630,0.170,0.000>)
VMD_sphere(<-0.0652,-0.0779,-0.0517>,0.0141,rgbt<1.000,1.000,1.000,0.000>)
VMD_sphere(<-0.0791,-0.1288,-0.0721>,0.0215,rgbt<0.700,0.200,0.100,0.000>)
VMD_sphere(<-0.0609,-0.1689,-0.0366>,0.0141,rgbt<1.000,1.000,1.000,0.000>)
VMD_sphere(<0.0434,-0.1790,0.0644>,0.0141,rgbt<1.000,1.000,1.000,0.000>)
VMD_sphere(<0.0814,-0.1372,0.0627>,0.0215,rgbt<0.700,0.200,0.100,0.000>)
VMD_sphere(<0.0668,-0.1001,0.0226>,0.0141,rgbt<1.000,1.000,1.000,0.000>)
VMD_sphere(<-0.1390,-0.0400,0.1447>,0.0141,rgbt<1.000,1.000,1.000,0.000>)
VMD_sphere(<-0.0860,-0.0399,0.1643>,0.0215,rgbt<0.700,0.200,0.100,0.000>)
VMD_sphere(<-0.0498,-0.0381,0.1209>,0.0141,rgbt<1.000,1.000,1.000,0.000>)
VMD_sphere(<0.0555,0.0915,-0.0854>,0.0141,rgbt<1.000,1.000,1.000,0.000>)
VMD_sphere(<0.0799,0.1265,-0.1226>,0.0215,rgbt<0.700,0.200,0.100,0.000>)
VMD_sphere(<0.0441,0.1684,-0.1352>,0.0141,rgbt<1.000,1.000,1.000,0.000>)
VMD_sphere(<-0.0604,0.0740,-0.0819>,0.0141,rgbt<1.000,1.000,1.000,0.000>)
VMD_sphere(<-0.0967,0.1016,-0.1153>,0.0215,rgbt<0.700,0.200,0.100,0.000>)
VMD_sphere(<-0.0741,0.1076,-0.1668>,0.0141,rgbt<1.000,1.000,1.000,0.000>)
VMD_sphere(<0.1508,0.0615,0.1210>,0.0141,rgbt<1.000,1.000,1.000,0.000>)
VMD_sphere(<0.1103,0.0981,0.1063>,0.0215,rgbt<0.700,0.200,0.100,0.000>)
VMD_sphere(<0.0741,0.0730,0.0708>,0.0141,rgbt<1.000,1.000,1.000,0.000>)
VMD_cylinder(<-0.0651655,-0.0779033,-0.051729>,<-0.0721252,-0.103338,-0.0619078>0.0042,rgbt<1.000,1.000,1.000,0.000>,1)
VMD_cylinder(<-0.0790846,-0.128774,-0.0720868>,<-0.0721252,-0.103338,-0.0619078>0.0042,rgbt<0.700,0.200,0.100,0.000>,1)
VMD_cylinder(<-0.0790846,-0.128774,-0.0720868>,<-0.0699954,-0.148827,-0.0543575>0.0042,rgbt<0.700,0.200,0.100,0.000>,1)
VMD_cylinder(<-0.0609062,-0.168879,-0.0366282>,<-0.0699954,-0.148827,-0.0543575>0.0042,rgbt<1.000,1.000,1.000,0.000>,1)
VMD_cylinder(<0.0434299,-0.179033,0.0644162>,<0.0624253,-0.158118,0.0635691>0.0042,rgbt<1.000,1.000,1.000,0.000>,1)
VMD_cylinder(<0.0814211,-0.137202,0.0627222>,<0.0624253,-0.158118,0.0635691>0.0042,rgbt<0.700,0.200,0.100,0.000>,1)
VMD_cylinder(<0.0814211,-0.137202,0.0627222>,<0.0741276,-0.118654,0.0426838>0.0042,rgbt<0.700,0.200,0.100,0.000>,1)
VMD_cylinder(<0.0668339,-0.100107,0.0226455>,<0.0741276,-0.118654,0.0426838>0.0042,rgbt<1.000,1.000,1.000,0.000>,1)
VMD_cylinder(<-0.138992,-0.0400298,0.144744>,<-0.112473,-0.0399745,0.154529>0.0042,rgbt<1.000,1.000,1.000,0.000>,1)
VMD_cylinder(<-0.0859547,-0.0399191,0.164316>,<-0.112473,-0.0399745,0.154529>0.0042,rgbt<0.700,0.200,0.100,0.000>,1)
VMD_cylinder(<-0.0859547,-0.0399191,0.164316>,<-0.0678961,-0.0389977,0.142588>0.0042,rgbt<0.700,0.200,0.100,0.000>,1)
VMD_cylinder(<-0.0498372,-0.0380759,0.120861>,<-0.0678961,-0.0389977,0.142588>0.0042,rgbt<1.000,1.000,1.000,0.000>,1)
VMD_cylinder(<0.0555215,0.0915122,-0.0854185>,<0.067694,0.108992,-0.104001>0.0042,rgbt<1.000,1.000,1.000,0.000>,1)
VMD_cylinder(<0.0798665,0.126471,-0.122583>,<0.067694,0.108992,-0.104001>0.0042,rgbt<0.700,0.200,0.100,0.000>,1)
VMD_cylinder(<0.0798665,0.126471,-0.122583>,<0.0619851,0.147428,-0.128916>0.0042,rgbt<0.700,0.200,0.100,0.000>,1)
VMD_cylinder(<0.044104,0.168385,-0.135249>,<0.0619851,0.147428,-0.128916>0.0042,rgbt<1.000,1.000,1.000,0.000>,1)
VMD_cylinder(<-0.0603646,0.0740328,-0.0818934>,<-0.0785303,0.0878022,-0.0986087>0.0042,rgbt<1.000,1.000,1.000,0.000>,1)
VMD_cylinder(<-0.0966961,0.101572,-0.115324>,<-0.0785303,0.0878022,-0.0986087>0.0042,rgbt<0.700,0.200,0.100,0.000>,1)
VMD_cylinder(<-0.0966961,0.101572,-0.115324>,<-0.0853946,0.104585,-0.141058>0.0042,rgbt<0.700,0.200,0.100,0.000>,1)
VMD_cylinder(<-0.074093,0.107599,-0.166791>,<-0.0853946,0.104585,-0.141058>0.0042,rgbt<1.000,1.000,1.000,0.000>,1)
VMD_cylinder(<0.15077,0.0614536,0.12102>,<0.130545,0.0797784,0.11366>0.0042,rgbt<1.000,1.000,1.000,0.000>,1)
VMD_cylinder(<0.110321,0.0981033,0.106299>,<0.0922339,0.0855527,0.0885677>0.0042,rgbt<0.700,0.200,0.100,0.000>,1)
VMD_cylinder(<0.110321,0.0981033,0.106299>,<0.130545,0.0797784,0.11366>0.0042,rgbt<0.700,0.200,0.100,0.000>,1)
VMD_cylinder(<0.0741472,0.0730019,0.0708368>,<0.0922339,0.0855527,0.0885677>0.0042,rgbt<1.000,1.000,1.000,0.000>,1)
// Mol[1] Rep[1] VDW
VMD_sphere(<0.0047,0.0078,-0.0102>,0.0642,rgbt<0.170,0.630,0.170,0.000>)
// End of POV-Ray 3.x generation 
