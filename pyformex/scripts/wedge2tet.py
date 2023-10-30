"""Convert wedge6 mesh to tet4"""

from pyformex.gui.draw import *

delay(1)
clear()
smoothwire()


def single_element():
    setShrink(0.7)
    W = Mesh(eltype='wedge6')
    draw(W, color=red)
    print(W.report())
    print("Volume: %s" % W.volume())

    V = W.convert('tet4-3l')
    clear()
    draw(V, color='cyan')
    drawNumbers(W.coords)
    print(V.volume())

    W1 = W.trl((1.5, 0, 0))
    V1 = W1.convert('tet4-3r')
    draw(V1, color='cyan')
    drawNumbers(W1.coords)
    print(V1.volume())



def full_mesh(nx, ny, d='d'):
    setShrink(0.7)
    M = Formex('4:0123').replic2(nx, ny).toMesh().convert('tri3-'+d)
    draw(M)
    W = M.extrude(2, dir=2, length=1.5).compact()
    W.setProp(np.random.randint(1, 7, W.nelems()))
    WA = draw(W)
    print(W.report())
    print("Volume: %s" % W.volume())
    print("Area: %s" % W.getBorderMesh().area())
    V = W.convert('tet4-3')
    draw(V, color='cyan')
    print(V.volume())
    #drawNumbers(V)
    if ack("Show border mesh?"):
        B = V.getBorderMesh()
        clear()
        draw(B)
        print(B.area())


if ask("Single element or full mesh?", ['Single', 'Full']) == 'Single':
    single_element()
else:
    full_mesh(3, 2, 'r')


exit()
