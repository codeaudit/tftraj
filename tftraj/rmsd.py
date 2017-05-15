import tensorflow as tf


def optimal_rotational_quaternion(r):
    """Just need the largest eigenvalue of this to minimize RMSD over rotations
    
    References
    ----------
    [1] http://dx.doi.org/10.1002/jcc.20110
    """
    # @formatter:off
    return [
        [r[0][0]+r[1][1]+r[2][2], r[1][2]-r[2][1],         r[2][0]-r[0][2],         r[0][1]-r[1][0]        ],
        [r[1][2]-r[2][1],         r[0][0]-r[1][1]-r[2][2], r[0][1]+r[1][0],         r[0][2]+r[2][0]        ],
        [r[2][0]-r[0][2],         r[0][1]+r[1][0],        -r[0][0]+r[1][1]-r[2][2], r[1][2]+r[2][1]        ],
        [r[0][1]-r[1][0],         r[0][2]+r[2][0],         r[1][2]+r[2][1],        -r[0][0]-r[1][1]+r[2][2]],
    ]
    # @formatter:on


def squared_deviation(frame, target):
    """Calculate squared deviation (n_atoms * RMSD^2) from `frame` to `target`

    First we compute `R` which is the ordinary cross-correlation of xyz coordinates.
    Turns out you can do a bunch of quaternion math to find an eigen-expression for finding optimal
    rotations. There aren't quaternions in tensorflow, so we use the handy formula for turning
    quaternions back into 4-matrices. This is the `F` matrix. We find its leading eigenvalue
    to get the MSD after optimal rotation. Note: *finding* the optimal rotation requires the values
    and vectors, but we don't care.
    
    Parameters
    ----------
    frame, target : Tensor, shape=(n_atoms, 3)
        Calculate the MSD between these two frames
        
    Returns
    -------
    sd : Tensor, shape=(0,)
        Divide by number of atoms and take the square root for RMSD
    """
    R = tf.matmul(frame, target, transpose_a=True, name='R')
    R_parts = [tf.unstack(t) for t in tf.unstack(R)]
    F_parts = optimal_rotational_quaternion(R_parts)
    F = tf.stack(F_parts, name='F')
    vals, vecs = tf.self_adjoint_eig(F, name='eig')
    # This isn't differentiable for some godforsaken reason.
    # vals = tf.self_adjoint_eigvals(F, name='vals')
    lmax = tf.unstack(vals)[-1]
    sd = tf.reduce_sum(frame ** 2 + target ** 2) - 2 * lmax
    return sd

def rmsd(frame, target, n_atoms):
    """Convenience function for actually returning the RMSD
    
    You should probably use squared_deviation when optimizing.
    """
    return tf.sqrt(squared_deviation(frame, target) / n_atoms)


def multi_sd(frames, target):
    return tf.map_fn(lambda x: squared_deviation(x, target), frames, name='MultiMSD')


def sum_sd(frames, target):
    return tf.reduce_sum(multi_sd(frames, target), name='SumMSD')
